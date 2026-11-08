# SnowLuma 平台特性文件

SnowLumaAdapter 是基於 SnowLuma 後端（NTQQ hook）建構的適配器，使用 OneBot v11 協議通訊。

---

## 文件資訊

- 對應模組版本: 0.3.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：SnowLuma 是基於 NTQQ hook 的 QQ 協議實現，API 全面向 NapCat 對齊，透過 OneBot v11 協議對外提供服務（預設端口：HTTP 3000、WS 3001）
- 適配器名稱：SnowLumaAdapter
- 支援的協議/API 版本：OneBot V11（官方動作目錄共 200 個動作，適配器全量覆蓋；全面相容 NapCat，可直接連接 NapCat 後端）
- 多帳戶支援：預設多帳戶架構，支援同時配置和運行多個帳戶
- 配置鍵名：`SnowLuma_Adapter`

### 與 OneBot11 適配器的關係

SnowLuma 使用 OB11 協議，標準動作與事件轉換與 OneBot11 適配器同構（OB12 標準動作名自動映射）。
主要差異：

1. **預設 client 模式**：主動連接 SnowLuma WS（`ws://127.0.0.1:3001`），無需公開網域監聽；另支援 server（反向 WS）/ http（API+輪詢）/ webhook（API+上報）共四種模式
2. **bot_id 自動識別**：無需在帳戶配置中填寫 QQ 號，適配器啟動後自動探測並維護 `self_id → account_name` 映射
3. **200 個動作全量封裝**：類型化方法 169 個（127 個通用擴展 + 42 個 SnowLuma 特有），其餘為 Core 直調 / ApiDSL 透傳 / 服務端別名，完整對照見適配器倉庫 [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)
4. **合併轉發擴展鏈路**：專用端點 + `upload_forward_msg`（上傳節點取 resid）+ `get_forward_msg`（解析轉發內容）三級回退

---

## 標準 Api 動作（Api DSL）

適配器將 OneBot12 標準動作名自動映射到 OB11 動作名，模組可跨平台統一呼叫：

| OB12 標準動作 | OB11 動作 | 說明 |
|--------------|-----------|------|
| get_self_info | get_login_info | 字段標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | 字段標準化 |
| delete_message | delete_msg | 撤回訊息 |
| leave_group | set_group_leave | 退出群 |
| upload_file | upload_group_file / upload_private_file | 扩展 group_id/user_id 可選參數 |

### 基本用法

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 取得機器人資訊
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# 撤回訊息
await snowluma.Api.delete_message(message_id=123456)

# 指定帳戶（多帳戶）
result = await snowluma.Api.Using("main").get_self_info()

# 服務端別名等少數動作透過 call() 逃生艙呼叫（SnowLuma/NapCat 通用）
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # upload_forward_msg 別名
```

---

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 使用預設帳戶發送
await snowluma.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶發送
await snowluma.Send.Using("main").To("group", group_id).Text("來自主帳戶的訊息")

# 鏈式修飾：@用戶 + 回覆
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("回覆訊息")
```

### 基礎發送方法

- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：發送圖片（支援 URL、Base64 或 bytes）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：發送語音訊息。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：發送影片訊息。
- `.Face(id: Union[str, int])`：發送 QQ 表情。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：發送檔案。
- `.MergeForward(nodes, title="合併聊天記錄")`：發送合併轉發訊息（見下節）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息（自動轉換為 OB11；純 node 段列表自動路由合併轉發）。
- `.Recall(message_id: Union[str, int])`：撤回訊息。

### 合併轉發

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "【1/3】標題\n正文…"}}],
        },
    },
]

# 發送合併轉發（三級回退，SnowLuma / NapCat 後端均適用）：
# ① send_group/private_forward_msg 專用端點（NapCat 原生，SnowLuma 兼容）
# ② upload_forward_msg 取 resid → send_msg 發 forward 段（SnowLuma 擴展鏈路）
# ③ send_msg 直發 node 段
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# 解析已收到的合併轉發訊息（入站 forward 段以 onebot11_forward 透傳，data.id 為 resid）
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### 群操作方法

以下方法需透過 `To("group", group_id)` 指定目標群：

- `.Kick(user_id, reject_add_request=False)`：踢出群成員。
- `.Ban(user_id, duration=1800)`：禁言群成員（秒），0 表示解禁。
- `.WholeBan(enable=True)`：開啟/關閉全體禁言。
- `.SetAdmin(user_id, enable=True)`：設定/取消群管理員。
- `.SetCard(user_id, card="")`：設定群名片。
- `.SetGroupName(name)`：修改群名稱。
- `.Leave(is_dismiss=False)`：退群（群主可解散）。
- `.SetTitle(user_id, title="")`：設定群頭銜。
- `.SetPortrait(file)`：設定群頭像。

### 拍一戳 / 社交

- `.GroupPoke(user_id)`：群內戳一戳（需 `To("group", group_id)`）。
- `.FriendPoke(user_id)`：好友戳一戳。
- `.SendPoke(user_id)`：發送戳一戳（通用）。
- `.SetMsgEmojiLike(message_id, emoji_id)`：訊息表情回應。

### QQ 空間

- `.QzoneMsg(content)`：發表 QQ 空間說說。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：點讚/取消點讚。
- `.QzoneComment(tid, content)`：評論。
- `.QzoneDelete(tid)`：刪除。

### 群檔案 / 訊息歷史 / 已讀狀態

- `.UploadGroupFile(file, name)`：上傳群檔案（需 `To("group", group_id)`）。
- `.GetGroupFileUrl(file_id)`：取得群檔案下載連結。
- `.GetGroupMsgHistory(message_id=0, count=20)`：取得群訊息歷史（message_id=0 從最新開始）。
- `.GetFriendMsgHistory(user_id, count=20)`：取得好友訊息歷史。
- `.MarkMsgAsRead(message_id)`：按訊息 ID 標記已讀。
- `.SetOnlineStatus(status)`：設定線上狀態。

### 發送到會話（SnowLuma 擴展，群聊/私聊自動路由）

- `.AIRecord(character, text, chat_type=1)`：發送 AI 語音到群（需 `To("group", group_id)`；角色來自 `Api.get_ai_characters`）。
- `.CustomFace(emoji_id, reply_to=None)`：發送帳號收藏表情（保留表情顯示樣式）。
- `.FlashMsg(fileset_id)`：發送閃傳訊息（對端收到後可下載）。
- `.ForwardSingle(message_id)`：轉發單條訊息到當前會話。
- `.TuwenArk(title, desc, jump_url, summary="[分享]", preview_url=...)`：發送圖文 Ark 卡片。

### 鏈式修飾方法（可組合使用）

- `.At(user_id: Union[str, int])`：@指定用戶（可多次呼叫）。
- `.AtAll()`：@全體成員。
- `.Reply(message_id: Union[str, int])`：回覆指定訊息。

---

## OB11 擴展動作（Api DSL）

官方動作目錄共 **200 個動作**，適配器類型化封裝 169 個（`OB11ExtensionApi` 127 個通用 + `SnowLumaExtensionApi` 42 個 SnowLuma 特有），其餘為 Core 直調 / ApiDSL 透傳 / 服務端別名，逐條狀態見[覆蓋對照表](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)。
全部動作均可透過 `Api.call("action_name", ...)` 直接呼叫（SnowLuma/NapCat 通用部分跨後端可移植）。分組概覽：

| 分組 | 代表動作 |
|------|----------|
| 拍一戳 / 社交 | send_poke / group_poke / friend_poke / send_like |
| 訊息回應 / 精華 | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| 已讀 / 狀態 | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| 訊息歷史 | get_group_msg_history / get_friend_msg_history |
| 群管理擴展 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo（含 cancel/complete/list）/ get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| 群標籤 / 管理設定 | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
| 好友 / 聯絡人 | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request（含處理） |
| 群檔案 | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file（含檔案夾刪除/重命名）/ move_group_file / trans_group_file / get_group_file_system_info |
| 群資訊 | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| 群相簿（列表） | get_group_album_list / get_group_album_media_list |
| QQ 空間 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| 合併轉發 / 單條轉發 | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark 卡片 / 小程式 | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| AI 語音 | get_ai_characters / get_ai_record / send_group_ai_record |
| 群公告 / 機型 / 裝扮 | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| 媒體 / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| 憑證 / 能力 | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| 工具 / 雜項 | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### 使用範例

```python
snowluma = sdk.adapter.get("snowluma")

# 已讀（按訊息 ID 定位）
await snowluma.Api.mark_msg_as_read(message_id=123)

# 語音轉文字（按訊息 ID 定位）
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# 表情回應詳情
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# 群公告
await snowluma.Api.send_group_notice(group_id=123456, content="公告", pinned=1)

# AI 語音
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="你好")
```

## SnowLuma 特有動作（SnowLumaExtensionApi）

以下動作為 SnowLuma 服務端特有（非 NapCat/Lagrange 通用），同樣以類型化方法提供：

### QQ 空間擴展

```python
# 說說詳情與一頁評論（需有訪問權限）
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# 修改已發說說的查看權限：1=所有人，4=好友，16=部分好友，64=僅自己，128=部分好友不可見
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# 拉黑/解除拉黑某人（機器人自己的空間黑名單）
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### 群相簿

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="相簿", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="相簿", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="拍得不錯")
await snowluma.Api.del_group_album_media(group_id=123456, album_id="a1", lloc="xxx")
```

### 系統表情

```python
result = await snowluma.Api.fetch_sys_faces()            # 完整目錄（按分組）
result = await snowluma.Api.search_sys_faces(query="微笑")  # 按名稱/別名/編號搜尋
result = await snowluma.Api.fetch_face_entity(face_id=1)   # 按編號查詢
result = await snowluma.Api.fetch_super_face_id(face_id=1) # 是否超級表情格式
```

### 流式介面

```python
# 分塊上傳檔案到機器人本地（新流 → 逐塊 → is_complete 合併，返回可發送的本地路徑）
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# 流式下載（file_info → file_chunk* → file_complete 分幀返回）
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### 閃傳 / 收藏表情 / 底層通道

```python
# QQ 閃傳：分享碼 → fileset_id → 發送/列表/直鏈
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# 收藏表情
await snowluma.Api.add_custom_face(file="https://a.gif")
result = await snowluma.Api.fetch_custom_face(count=10, return_type="url")
await snowluma.Api.send_custom_face(emoji_id="emoji_id_or_md5", group_id=123456)

# 底層通道（高階用法）
await snowluma.Api.send_packet(cmd="Oidb.0xxxx", data="hex...")
await snowluma.Api.request_decrypt_key(db_path="./db")
await snowluma.Api.bot_exit()
```

---

## 事件類型映射

### 標準 OB12 映射

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊訊息 |
| message_type: group | `group` | 群聊訊息 |
| notice_type: group_upload | `group_file_upload` | 群檔案上傳 |
| notice_type: group_admin | `group_admin_change` | 群管理員變動 |
| notice_type: group_increase | `group_member_increase` | 群成員增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成員減少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友增加 |
| notice_type: friend_delete | `friend_decrease` | 好友刪除 |
| notice_type: group_recall / friend_recall | `message_recall` | 訊息撤回 |

### 平台特有事件與擴展段

- 平台特有事件（poke/honor 等）使用 `snowluma_` 前綴的 detail_type
- 未識別的 CQ 碼類型以 `onebot11_{type}` 前綴透傳（協議級前綴）
- 入站合併轉發訊息段為 `onebot11_forward`（`data.id` 為 resid，可用 `Api.get_forward_msg(id=...)` 解析內容）

### 擴展欄位說明

- 所有特有欄位均以 `snowluma_` 前綴標識
- 保留原始事件資料在 `snowluma_raw` 欄位
- 保留原始事件類型在 `snowluma_raw_type` 欄位

---

## 事件擴展方法

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 取得 SnowLuma 完整原始事件資料 |
| `get_raw_self_id()` | `str` | 取得原始 self_id（Bot 的 QQ 號） |
| `get_sender_info()` | `dict` | 取得完整的發送者資訊（包含 nickname、role、level 等） |
| `get_sender_role()` | `str` | 取得發送者在群內的角色（owner/admin/member） |
| `get_sender_level()` | `int` | 取得發送者等級 |
| `get_sender_title()` | `str` | 取得發送者群頭銜 |
| `is_system_message()` | `bool` | 判斷是否為系統訊息 |

---

## 配置選項

SnowLuma 適配器採用多帳戶架構，每個帳戶獨立配置。配置鍵名為 `SnowLuma_Adapter`。

### 帳戶配置欄位

| 欄位 | 類型 | 必填 | 默認值 | 說明 |
|------|------|------|--------|------|
| `mode` | `str` | 否 | `"client"` | `client`(主動連 WS) / `server`(反向 WS) / `http`(HTTP API+輪詢) / `webhook`(HTTP API+上報) |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 位址（SnowLuma 默認 WS 端口 3001） |
| `token` | `str` | 否 | `""` | 訪問權杖（Bearer 認證） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路徑 |
| `http_url` | `str` | 否 | `"http://127.0.0.1:3000"` | http/webhook 模式的 API 位址 |
| `poll_interval` | `float` | 否 | `1.0` | http 模式事件輪詢間隔（秒） |
| `webhook_path` | `str` | 否 | `"/snowluma_{account}"` | webhook 模式上報路由前綴 |
| `enabled` | `bool` | 否 | `true` | 是否啟用該帳戶 |
| `name` | `str` | 否 | `""` | 帳戶備註名稱 |

> bot_id（QQ 號）無需配置：適配器連接後自動識別，並維護 `self_id → account_name` 映射，
> `event.reply()` 自動路由到來源帳戶。

### 配置範例

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

## 發送方法回傳值

所有發送方法均回傳一個 Task 物件，可以直接 await 取得發送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

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

### 多帳戶發送語法

```python
# 帳戶選擇方法
await snowluma.Send.Using("main").To("group", 123456).Text("主帳戶訊息")

# API呼叫方式
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id 自動映射

適配器會自動建立 OneBot `self_id`（QQ號）到 `account_name` 的映射關係，用於事件回路由：

```python
@message.on_message()
async def handler(event):
    # 自動路由到正確的帳戶
    await event.reply("自動路由到來源帳戶")
```