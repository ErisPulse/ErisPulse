# SnowLuma平台特性文档

SnowLumaAdapter 是基于 SnowLuma 后端（NTQQ hook）构建的适配器，使用 OneBot v11 协议通信。

---

## 文档信息

- 对应模块版本: 0.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：SnowLuma 是基于 NTQQ hook 的 QQ 协议实现，API 全面向 NapCat 对齐，通过 OneBot v11 协议对外提供服务（默认端口：HTTP 3000、WS 3001）
- 适配器名称：SnowLumaAdapter
- 支持的协议/API版本：OneBot V11（含 SnowLuma 扩展动作，全面兼容 NapCat，可直接连接 NapCat 后端）
- 多账户支持：默认多账户架构，支持同时配置和运行多个账户
- 配置键名：`SnowLuma_Adapter`

### 与 OneBot11 适配器的关系

SnowLuma 使用 OB11 协议，标准动作与事件转换与 OneBot11 适配器同构（OB12 标准动作名自动映射）。
主要差异：

1. **默认 client 模式**：主动连接 SnowLuma WS（`ws://127.0.0.1:3001`），无需公网监听
2. **bot_id 自动识别**：无需在账户配置中填写 QQ 号，适配器启动后自动探测并维护 `self_id → account_name` 映射
3. **109 个扩展动作**：拍一戳、QQ空间、群文件/群相册、消息历史、精华、已读状态等 SnowLuma/NapCat 兼容扩展
4. **合并转发扩展链路**：专用端点 + `upload_forward_msg`（上传节点取 resid）+ `get_forward_msg`（解析转发内容）三级回退

---

## 标准Api动作（Api DSL）

适配器将 OneBot12 标准动作名自动映射到 OB11 动作名，模块可跨平台统一调用：

| OB12 标准动作 | OB11 动作 | 说明 |
|--------------|-----------|------|
| get_self_info | get_login_info | 字段标准化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | 字段标准化 |
| delete_message | delete_msg | 撤回消息 |
| leave_group | set_group_leave | 退出群 |
| upload_file | upload_group_file / upload_private_file | 扩展 group_id/user_id 可选参数 |

### 基本用法

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 获取机器人信息
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# 撤回消息
await snowluma.Api.delete_message(message_id=123456)

# 指定账户（多账户）
result = await snowluma.Api.Using("main").get_self_info()

# 扩展动作通过 call() 逃生舱调用（SnowLuma/NapCat 通用）
result = await snowluma.Api.call("send_poke", group_id=123, user_id=456)
```

---

## 支持的消息发送类型

所有发送方法均通过链式语法实现，例如：

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 使用默认账户发送
await snowluma.Send.To("group", group_id).Text("Hello World!")

# 指定特定账户发送
await snowluma.Send.Using("main").To("group", group_id).Text("来自主账户的消息")

# 链式修饰：@用户 + 回复
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回复消息")
```

### 基础发送方法

- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：发送图片（支持 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：发送语音消息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：发送视频消息。
- `.Face(id: Union[str, int])`：发送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：发送文件。
- `.MergeForward(nodes, title="合并聊天记录")`：发送合并转发消息（见下节）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：发送 OneBot12 格式消息（自动转换为 OB11；纯 node 段列表自动路由合并转发）。
- `.Recall(message_id: Union[str, int])`：撤回消息。

### 合并转发

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "【1/3】标题\n正文…"}}],
        },
    },
]

# 发送合并转发（三级回退，SnowLuma / NapCat 后端均适用）：
# ① send_group/private_forward_msg 专用端点（NapCat 原生，SnowLuma 兼容）
# ② upload_forward_msg 取 resid → send_msg 发 forward 段（SnowLuma 扩展链路）
# ③ send_msg 直发 node 段
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# 解析已收到的合并转发消息（入站 forward 段以 onebot11_forward 透传，data.id 为 resid）
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### 群操作方法

以下方法需通过 `To("group", group_id)` 指定目标群：

- `.Kick(user_id, reject_add_request=False)`：踢出群成员。
- `.Ban(user_id, duration=1800)`：禁言群成员（秒），0 表示解禁。
- `.WholeBan(enable=True)`：开启/关闭全员禁言。
- `.SetAdmin(user_id, enable=True)`：设置/取消群管理员。
- `.SetCard(user_id, card="")`：设置群名片。
- `.SetGroupName(name)`：修改群名称。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：设置群头衔。
- `.SetPortrait(file)`：设置群头像。

### 拍一戳 / 社交

- `.GroupPoke(user_id)`：群内戳一戳（需 `To("group", group_id)`）。
- `.FriendPoke(user_id)`：好友戳一戳。
- `.SendPoke(user_id)`：发送戳一戳（通用）。
- `.SetMsgEmojiLike(message_id, emoji_id)`：消息表情回应。

### QQ空间

- `.QzoneMsg(content)`：发表 QQ 空间说說。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：点赞/取消点赞。
- `.QzoneComment(tid, content)`：评论。
- `.QzoneDelete(tid)`：删除。

### 群文件 / 消息历史 / 已读状态

- `.UploadGroupFile(file, name)`：上传群文件（需 `To("group", group_id)`）。
- `.GetGroupFileUrl(file_id)`：获取群文件下载链接。
- `.GetGroupMsgHistory(message_seq=0, count=20)`：获取群消息历史。
- `.GetFriendMsgHistory(user_id, count=20)`：获取好友消息历史。
- `.MarkMsgAsRead()`：标记当前会话已读。
- `.SetOnlineStatus(status)`：设置在线状态。

### 链式修饰方法（可组合使用）

- `.At(user_id: Union[str, int])`：@指定用户（可多次调用）。
- `.AtAll()`：@全体成员。
- `.Reply(message_id: Union[str, int])`：回复指定消息。

---

## OB11 扩展动作（Api DSL）

除标准动作外，`OB11ExtensionApi` 混入提供了 60+ 个类型化扩展方法，全部 109 个扩展动作均可通过
`Api.call("action_name", ...)` 直接调用（SnowLuma/NapCat 通用）。分组概览：

| 分组 | 代表动作 |
|------|----------|
| 拍一戳 / 社交 | send_poke / group_poke / friend_poke / send_like |
| 消息回应 / 精华 | set_msg_emoji_like / get_emoji_likes / set_essence_msg / get_essence_msg_list |
| 已读 / 状态 | mark_msg_as_read / mark_group_msg_as_read / mark_all_as_read / set_online_status / set_input_status |
| 消息历史 | get_group_msg_history / get_friend_msg_history |
| 群管理扩展 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo / get_group_info_ex / get_group_shut_list / get_group_at_all_remain |
| 好友 / 联系人 | set_friend_remark / get_unidirectional_friend_list / get_friends_with_category / get_recent_contact |
| 群文件 | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file |
| 群相册 | get_group_album_list / get_group_album_media_list |
| QQ空间 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds |
| 合并转发 | get_forward_msg / upload_forward_msg |
| 媒体 / OCR | ocr_image / get_image |

---

## 事件类型映射

### 标准 OB12 映射

| OB11 原始类型 | 转换后 detail_type | 说明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊消息 |
| message_type: group | `group` | 群聊消息 |
| notice_type: group_upload | `group_file_upload` | 群文件上传 |
| notice_type: group_admin | `group_admin_change` | 群管理员变动 |
| notice_type: group_increase | `group_member_increase` | 群成员增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成员减少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友添加 |
| notice_type: friend_delete | `friend_decrease` | 好友删除 |
| notice_type: group_recall / friend_recall | `message_recall` | 消息撤回 |

### 平台特有事件与扩展段

- 平台特有事件（poke/honor 等）使用 `snowluma_` 前缀的 detail_type
- 未识别的 CQ 码类型以 `onebot11_{type}` 前缀透传（协议级前缀）
- 入站合并转发消息段为 `onebot11_forward`（`data.id` 为 resid，可用 `Api.get_forward_msg(id=...)` 解析内容）

### 扩展字段说明

- 所有特有字段均以 `snowluma_` 前缀标识
- 保留原始事件数据在 `snowluma_raw` 字段
- 保留原始事件类型在 `snowluma_raw_type` 字段

---

## 事件扩展方法

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 获取 SnowLuma 完整原始事件数据 |
| `get_raw_self_id()` | `str` | 获取原始 self_id（Bot 的 QQ 号） |
| `get_sender_info()` | `dict` | 获取完整的发送者信息（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 获取发送者在群内的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 获取发送者等级 |
| `get_sender_title()` | `str` | 获取发送者群头衔 |
| `is_system_message()` | `bool` | 判断是否为系统消息 |

---

## 配置选项

SnowLuma 适配器采用多账户架构，每个账户独立配置。配置键名为 `SnowLuma_Adapter`。

### 账户配置字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `mode` | `str` | 否 | `"client"` | 运行模式：`"client"`（主动连接，推荐）或 `"server"`（被动监听） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 地址（SnowLuma 默认 WS 端口 3001） |
| `token` | `str` | 否 | `""` | 访问令牌（Bearer 认证） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路径 |
| `enabled` | `bool` | 否 | `true` | 是否启用该账户 |
| `name` | `str` | 否 | `""` | 账户备注名称 |

> bot_id（QQ 号）无需配置：适配器连接后自动识别，并维护 `self_id → account_name` 映射，
> `event.reply()` 自动路由到来源账户。

### 配置示例

```toml
[SnowLuma_Adapter.accounts.main]
mode = "client"
url = "ws://127.0.0.1:3001"
token = ""
enabled = true

[SnowLuma_Adapter.accounts.second]
mode = "client"
url = "ws://192.168.1.100:3001"
token = "second_token"
enabled = true
```

---

## 发送方法返回值

所有发送方法均返回一个 Task 对象，可以直接 await 获取发送结果。返回结果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "snowluma_raw": {...}
}
```

### 多账户发送语法

```python
# 账户选择方法
await snowluma.Send.Using("main").To("group", 123456).Text("主账户消息")

# API调用方式
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id 自动映射

适配器会自动建立 OneBot `self_id`（QQ号）到 `account_name` 的映射关系，用于事件回路由：

```python
@message.on_message()
async def handler(event):
    # 自动路由到正确的账户
    await event.reply("自动路由到来源账户")
```
