# SnowLuma平台特性文档

SnowLumaAdapter 是基于 SnowLuma 后端（NTQQ hook）构建的适配器，使用 OneBot v11 协议通信。作为 `ErisPulse-OneBot11Adapter[snowluma]` 可选扩展安装（`pip install "ErisPulse-OneBot11Adapter[snowluma]"`）。

---

## 文档信息

- 对应模块版本: 0.3.4
- 维护者: ErisPulse
- 协议版本: OneBot v11（NapCat/go-cqhttp 兼容扩展）
- 最后更新: 2026-11-10

## 基本信息

- 平台简介：SnowLuma 是基于 NTQQ hook 的 QQ 协议实现，API 全面向 NapCat 对齐，通过 OneBot v11 协议对外提供服务（默认端口：HTTP 3000、WS 3001）
- 适配器名称：SnowLumaAdapter
- 支持的协议/API版本：OneBot V11（官方动作目录共 200 个动作，适配器全量覆盖；全面兼容 NapCat，可直接连接 NapCat 后端）
- 多账户支持：默认多账户架构，支持同时配置和运行多个账户
- 配置键名：`SnowLuma_Adapter`
- i18n：支持 5 语言（zh-CN / zh-TW / en / ja / ru）

### 与 OneBot11 适配器的关系

SnowLuma 使用 OB11 协议，标准动作与事件转换与 OneBot11 适配器同构（OB12 标准动作名自动映射）。
主要差异：

1. **默认 client 模式**：主动连接 SnowLuma WS（`ws://127.0.0.1:3001`），无需公网监听；另支持 server（反向 WS）/ http（API+轮询）/ webhook（API+上报）共四种模式
2. **bot_id 自动识别**：无需在账户配置中填写 QQ 号，适配器启动后自动探测并维护 `self_id → account_name` 映射
3. **200 个动作全量封装**：类型化方法 169 个（127 个通用扩展 + 42 个 SnowLuma 特有），其余为 Core 直调 / ApiDSL 透传 / 服务端别名，完整对照见适配器仓库 [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)
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

# upload_file 扩展参数（OB11 文件上传绑定目标，group_id/user_id 可选）
await snowluma.Api.upload_file(type="path", name="doc.pdf", path="./doc.pdf", group_id="123456")
await snowluma.Api.upload_file(type="url", name="img.jpg", url="https://...", user_id="789")

# 指定账户（多账户）
result = await snowluma.Api.Using("main").get_self_info()

# 服务端别名等少数动作通过 call() 逃生舱调用（SnowLuma/NapCat 通用）
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # upload_forward_msg 别名
```

> **命名约定**：OB11 协议扩展直接用动作名（`send_poke`），不加 `snowluma.` 前缀。只有真正平台独有的功能才用 `{prefix}.xxx`。

## 标准化对齐

本节说明适配器与 ErisPulse 标准化规范对齐的行为。规范详情参见 SDK 文档《请求操作规范》（`docs/zh-CN/standards/request-action-spec.md`）与《API 响应规范》（`docs/zh-CN/standards/api-response.md`）。

### 请求事件处理（0.3.3 起）

适配器按请求操作规范实现请求事件的接收与响应（与 OneBot11 适配器同构）：

- **上下文留存**：事件入口将 `request_id` 映射到 `{request_type, sub_type, group_id, account, ts}` 并缓存（TTL 3600 秒、上限 512 条，请求处理成功后清理），供后续 `accept()`/`reject()` 路由使用
- **端点路由优先级**：`accept()`/`reject()` 的 kwargs 显式传参（`request_type`/`sub_type`/`group_id` 为保留名）> 事件留存上下文 > 回退好友端点（`set_friend_add_request`）并输出 WARNING
- **群邀请/加群请求**：`request_type == "group"` 时正确路由到 `set_group_add_request`（加群 `sub_type="add"`、邀请 `sub_type="invite"`）
- **废弃说明**：通过私有参数 `_request_type` 指定请求类型的方式已废弃，传入会被忽略

### call_api 错误码

- HTTP 调用失败（连接异常/超时）返回 `retcode=33001` 标准失败响应
- 响应格式异常（无法解析为标准结构）返回 `retcode=34100`，原始数据保留在 `snowluma_raw` 字段

| retcode | 含义 | 触发场景 |
|---------|------|----------|
| 0 | 成功 | 动作执行成功 |
| 33001 | 网络错误 | HTTP 调用失败、API 调用超时 |
| 34100 | 平台错误 | 响应格式异常（原始数据保留在 `snowluma_raw`） |

### 账户字段双兼容与 send_context

- `call_api` 同时接受标准字段 `account_id` 与旧字段名 `_account_id`（标准名优先）；框架 ApiDSL 自动适配，模块代码推荐使用 `account_id`
- Send DSL 全方法读取 `send_context`：事件链内自动使用当前事件来源账户，显式 `Using()` 指定的账户优先

### 事件字段规范化

- meta 事件顶层 `type` 统一为 `"meta"`（原 `meta_event` 不再使用）
- 所有特有字段均以 `snowluma_` 前缀标识，原始数据保留在 `snowluma_raw`

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

- `.QzoneMsg(content)`：发表 QQ 空间说说。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：点赞/取消点赞。
- `.QzoneComment(tid, content)`：评论。
- `.QzoneDelete(tid)`：删除。

### 群文件 / 消息历史 / 已读状态

- `.UploadGroupFile(file, name)`：上传群文件（需 `To("group", group_id)`）。
- `.GetGroupFileUrl(file_id)`：获取群文件下载链接。
- `.GetGroupMsgHistory(message_id=0, count=20)`：获取群消息历史（message_id=0 从最新开始）。
- `.GetFriendMsgHistory(user_id, count=20)`：获取好友消息历史。
- `.MarkMsgAsRead(message_id)`：按消息 ID 标记已读。
- `.SetOnlineStatus(status)`：设置在线状态。

### 发送到会话（SnowLuma 扩展，群聊/私聊自动路由）

- `.AIRecord(character, text, chat_type=1)`：发送 AI 语音到群（需 `To("group", group_id)`；角色来自 `Api.get_ai_characters`）。
- `.CustomFace(emoji_id, reply_to=None)`：发送账号收藏表情（保留表情显示样式）。
- `.FlashMsg(fileset_id)`：发送闪传消息（对端收到后可下载）。
- `.ForwardSingle(message_id)`：转发单条消息到当前会话。
- `.TuwenArk(title, desc, jump_url, summary="[分享]", preview_url=...)`：发送图文 Ark 卡片。

### 更多 Send 便捷方法

| 方法 | 对应动作 | 说明 |
|------|---------|------|
| `.GroupReaction(msg_id, emoji_id)` | `set_group_reaction` | 群表情回应 |
| `.SetEssenceMsg(msg_id)` | `set_essence_msg` | 设置精华消息 |
| `.DeleteEssenceMsg(msg_id)` | `delete_essence_msg` | 移除精华消息 |
| `.SetFriendRemark(uid, remark)` | `set_friend_remark` | 设置好友备注 |
| `.OcrImage(image)` | `ocr_image` | OCR 图片识别 |
| `.GetImage(file)` | `get_image` | 获取图片信息 |
| `.GetRecord(file)` | `get_record` | 获取语音信息 |
| `.FetchPttText(message_id)` | `fetch_ptt_text` | 语音转文字 |

### 链式修饰方法（可组合使用）

- `.At(user_id: Union[str, int])`：@指定用户（可多次调用）。
- `.AtAll()`：@全体成员。
- `.Reply(message_id: Union[str, int])`：回复指定消息。

---

## OB11 扩展动作（Api DSL）

官方动作目录共 **200 个动作**，适配器类型化封装 169 个（`OB11ExtensionApi` 127 个通用 + `SnowLumaExtensionApi` 42 个 SnowLuma 特有），其余为 Core 直调 / ApiDSL 透传 / 服务端别名，逐条状态见适配器仓库 [覆盖对照表](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)。
全部动作均可通过 `Api.call("action_name", ...)` 直接调用（SnowLuma/NapCat 通用部分跨后端可移植）。分组概览：

| 分组 | 代表动作 |
|------|----------|
| 拍一戳 / 社交 | send_poke / group_poke / friend_poke / send_like |
| 消息回应 / 精华 | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| 已读 / 状态 | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| 消息历史 | get_group_msg_history / get_friend_msg_history |
| 群管理扩展 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo（含 cancel/complete/list）/ get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| 群标签 / 管理设置 | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
| 好友 / 联系人 | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request（含处理） |
| 群文件 | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file（含文件夹删除/重命名）/ move_group_file / trans_group_file / get_group_file_system_info |
| 群信息 | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| 群相册（列表） | get_group_album_list / get_group_album_media_list |
| QQ空间 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| 合并转发 / 单条转发 | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark 卡片 / 小程序 | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| AI 语音 | get_ai_characters / get_ai_record / send_group_ai_record |
| 群公告 / 机型 / 装扮 | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| 媒体 / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| 凭证 / 能力 | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| 工具 / 杂项 | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### 使用示例

```python
snowluma = sdk.adapter.get("snowluma")

# 已读（按消息 ID 定位）
await snowluma.Api.mark_msg_as_read(message_id=123)

# 语音转文字（按消息 ID 定位）
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# 表情回应详情
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# 群公告
await snowluma.Api.send_group_notice(group_id=123456, content="公告", pinned=1)

# AI 语音
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="你好")
```

## SnowLuma 特有动作（SnowLumaExtensionApi）

以下动作为 SnowLuma 服务端特有（非 NapCat/Lagrange 通用），同样以类型化方法提供：

### QQ 空间扩展

```python
# 说说详情与一页评论（需有访问权限）
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# 修改已发说说的查看权限：1=所有人，4=好友，16=部分好友，64=仅自己，128=部分好友不可见
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# 拉黑/解除拉黑某人（机器人自己的空间黑名单）
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### 群相册

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="相册", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="相册", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="拍得不错")
await snowluma.Api.del_group_album_media(group_id=123456, album_id="a1", lloc="xxx")
```

### 系统表情

```python
result = await snowluma.Api.fetch_sys_faces()            # 完整目录（按分组）
result = await snowluma.Api.search_sys_faces(query="微笑")  # 按名称/别名/编号搜索
result = await snowluma.Api.fetch_face_entity(face_id=1)   # 按编号查询
result = await snowluma.Api.fetch_super_face_id(face_id=1) # 是否超级表情格式
```

### 流式接口

```python
# 分块上传文件到机器人本地（新流 → 逐块 → is_complete 合并，返回可发送的本地路径）
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# 流式下载（file_info → file_chunk* → file_complete 分帧返回）
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### 闪传 / 收藏表情 / 底层通道

```python
# QQ 闪传：分享码 → fileset_id → 发送/列表/直链
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# 收藏表情
await snowluma.Api.add_custom_face(file="https://a.gif")
result = await snowluma.Api.fetch_custom_face(count=10, return_type="url")
await snowluma.Api.send_custom_face(emoji_id="emoji_id_or_md5", group_id=123456)

# 底层通道（高级用法）
await snowluma.Api.send_packet(cmd="Oidb.0xxxx", data="hex...")
await snowluma.Api.request_decrypt_key(db_path="./db")
await snowluma.Api.bot_exit()
```

---

## 事件类型映射

### 标准 OB12 映射

| OB11 原始类型 | 转换后 detail_type | 说明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊消息 |
| message_type: group | `group` | 群聊消息 |
| request_type: friend | `friend` | 好友请求 |
| request_type: group | `group` | 群请求（加群/邀请） |
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
- meta 事件顶层 `type` 统一为 `"meta"`

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
| `mode` | `str` | 否 | `"client"` | `client`(主动连 WS) / `server`(反向 WS) / `http`(HTTP API+轮询) / `webhook`(HTTP API+上报) |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 地址（SnowLuma 默认 WS 端口 3001） |
| `token` | `str` | 否 | `""` | 访问令牌（Bearer 认证） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路径 |
| `http_url` | `str` | 否 | `"http://127.0.0.1:3000"` | http/webhook 模式的 API 地址 |
| `poll_interval` | `float` | 否 | `1.0` | http 模式事件轮询间隔（秒） |
| `webhook_path` | `str` | 否 | `"/snowluma_{account}"` | webhook 模式上报路由前缀 |
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
