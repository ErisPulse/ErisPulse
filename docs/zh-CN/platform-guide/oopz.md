# Oopz 平台特性文档

## 文档信息

| 项目 | 内容 |
|---|---|
| 模块版本 | 0.1.0 |
| 平台标识 | `oopz` |
| 维护者 | ErisPulse 团队 |
| 最后更新 | 2026-11-13 |

> [!IMPORTANT]
> 本项目与 Oopz 没有任何关系（未获官方授权、非官方合作、官方不提供支持）。Oopz 无官方机器人平台，本适配器基于社区逆向协议以**用户账号身份**接入，随时可能失效，请使用小号。详见 README 声明与风险提示。

## 基本信息

- 适配器类：`OopzAdapter`（entry-point `oopz`）
- 接入方式：WebSocket（`wss://ws.oopz.cn`）+ REST 网关（`https://gateway.oopz.cn`），RSA 签名请求头 + JWT
- 凭据：「账密二选一」——`password`（手机号+密码+客户端私钥，自动登录续期，**推荐**）或 `token`（uid/JWT/device_id/私钥四件套，仅密码登录被风控时的备用，JWT 过期需手动重新提取）
- 多账户：支持（`[Oopz_Adapter.accounts.<name>]`），事件 `self.account_id` 标记来源
- 框架软依赖：ErisPulse ≥ 2.7.1

## 会话模型

| ErisPulse 目标 | Oopz 概念 | 说明 |
|---|---|---|
| `Send.To("group", <频道ID>)` | 频道（channel） | 域由适配器经「channel→area 缓存 + 已加入域扫描」自动解析 |
| `Send.To("user", <对方UID>)` | 私信会话 | 自动 `PATCH /client/v1/chat/v1/to` 开会话并缓存 sessionId |
| `guild_id` 字段 / guild 语义 | 域（area） | 域级操作走 `get_guild_*` 与 `oopz.*` 管理扩展 |

## 标准化对齐（0.1.0）

### 错误码规范

| retcode | 含义 |
|---|---|
| 0 | 成功 |
| 10002 | 不支持的动作/消息段降级（语音视频文件发送、upload_file、keyboard 等） |
| 10003 | 参数缺失/不合法（如频道无法定位所属域） |
| 33001 | 网络异常/限流（429 尊重 Retry-After 重试一次） |
| 34100 | 平台返回失败（原始响应在 `oopz_raw`） |
| 34005 | 账户未解析（未配置或未建立会话） |

### 响应结构

所有响应含 `status / retcode / data / message_id / message / oopz_raw`；发送响应 `message_id` 取自平台返回的 `messageId`；`data.self_info.user_id` 在 `get_self_info` 中回填。

### 事件字段完备性

- 所有事件必备 `id / time / type / detail_type / sub_type / platform / self`，且 `oopz_raw` + `oopz_raw_type` 永远存在
- 消息事件顶层必带 `message_id`；时间戳微秒字符串统一归一为秒
- 事件 `id` 账户域去重（`<account>:<类型>:<平台ID>`）
- 未知事件转 `type="unknown"` + `warning`，不静默丢弃
- 协议内部帧（握手/认证/心跳/订阅）不产生平台事件

### 降级语义

- `voice/audio/video/file` 发送段 → `retcode=10002`（平台仅支持图片上传），不抛异常
- `guild` 发送目标 → `retcode=10003`（请指定频道）
- token 模式 JWT 失效 → `retcode=34100` 提示更新凭据；password 模式自动重登后重试一次

## 支持的消息发送类型

| 方法 | 平台实现 |
|---|---|
| `Text` | 文本（text/content 双写） |
| `Image` | COS 签名票上传（仅图片），文本占位符 `![IMAGEw{w}h{h}]({fileKey})` + attachments |
| `At / AtAll / Reply` | `mentionList` / `isMentionAll` / `referenceMessageId` |
| `Important()` 修饰符 | `styleTags=["IMPORTANT"]` 公告样式 |
| `Recall(messageId)` | `recallGim`（频道）/ `recallIm`（私信，仅撤回自己发的） |
| `Raw_ob12` | OneBot12 段 → 平台 payload（text/mention/mention_all/reply/image；其余段降级 10002） |
| Voice/Video/File/Keyboard | 不支持 → 10002 |

## 标准 API 动作（ApiDSL）

### 支持的标准动作

`get_self_info`、`get_user_info`、`get_friend_list`、`get_group_info`（频道+所属域合并信息）、`get_group_list`（已加入域的频道扁平表）、`get_guild_info`、`get_guild_list`、`get_channel_list`、`get_guild_members`、`delete_message`（需 `channel_id` 或 `user_id` 上下文）、`get_file`（附件 URL → base64）、`leave_guild`、`get_status`、`get_version`、`get_supported_actions`

### 不支持的标准动作（retcode=10002）

`send_message`（走 Send DSL）、`upload_file`、`get_latest_events`、`set_group_name`、`set_group_admin`、`set_group_leave`、`set_group_card`、`leave_group`、`leave_channel`

### 平台扩展动作（oopz.*）

| 动作 | 必填参数 | 说明 |
|---|---|---|
| `oopz.create_channel` | `area_id, name` | 可选 `channel_type/group_id/secret/max_member` |
| `oopz.delete_channel` | `area_id, channel_id` | |
| `oopz.mute_member` / `oopz.unmute_member` | `area_id, user_id` | 禁言，`duration` 分钟数自动吸附档位（5分钟/1小时/1天/3天/7天） |
| `oopz.mute_mic` / `oopz.unmute_mic` | `area_id, user_id` | 禁麦 |
| `oopz.kick_member` | `area_id, user_id` | 移出域 |
| `oopz.block_user` / `oopz.unblock_user` | `area_id, user_id` | 域黑名单 |
| `oopz.get_area_members` | `area_id` | 可选 `offset_start/offset_end` |
| `oopz.get_assignable_roles` | `area_id, target_id` | 可分配身份组 |
| `oopz.assign_role` / `oopz.revoke_role` | `area_id, target_id, role_id` | 内部读全量角色后整体提交 |
| `oopz.react_message` / `oopz.unreact_message` | `message_id, channel_id, emoji` | 可选 `user_id`（私信）/`area_id` |
| `oopz.get_reactions` | `message_id` | 可选 `message_ids`（≤50）/`user_id` |
| `oopz.get_reaction_persons` | `message_id, channel_id, emoji` | 回应者分页 |
| `oopz.top_message` | `message_id, area_id, channel_id` | 置顶/取消（`cancel=True`） |
| `oopz.get_history_messages` | `area_id, channel_id` | 可选 `size`（默认 50） |
| `oopz.get_friend_requests` | — | 好友申请列表 |
| `oopz.respond_friend_request` | `target, friend_request_id, agree` | 审批（一般用 Request DSL） |

## 好友申请处理

- 事件：`request/friend`，`request_id` 为**无状态复合键** `<target>:<friendRequestId>`
- `event.approve()` / `event.reject()` → POST `/client/v1/friendship/v1/response`
- 单端点同构，无需请求类型上下文留存表

## 发送方法返回值

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "14283..."},
  "message_id": "14283...",
  "message": "",
  "oopz_raw": {"messageId": "14283...", "timestamp": "..."}
}
```

## 特有事件类型

- 消息事件扩展字段：`oopz_area_id`、`guild_id`（频道消息）；`oopz_reference_message_id`（回复）
- 通知扩展：`oopz_edited_text`、`oopz_emoji`、`oopz_reaction_type`、`oopz_persons`、`oopz_from_channel`、`oopz_channel_name`、`oopz_channel_type`、`oopz_area_name`、`oopz_role_id`、`oopz_role_name`、`oopz_ban_until`、`oopz_login_state`
- `EventMixin` 便捷方法：`get_raw_event()`、`get_area_id()`、`get_edited_text()`、`get_emoji()`、`get_reaction_type()`、`get_voice_persons()`
