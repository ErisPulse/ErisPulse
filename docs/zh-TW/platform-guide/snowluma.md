# SnowLuma 平台特性文件

SnowLumaAdapter 是基於 SnowLuma 後端（NTQQ hook）所建構的適配器，使用 OneBot v11 協議進行通訊。

---

## 文件資訊

- 對應模組版本: 0.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：SnowLuma 是基於 NTQQ hook 的 QQ 協議實現，API 全面向 NapCat 對齊，透過 OneBot v11 協議對外提供服務（預設端口：HTTP 3000、WS 3001）
- 適配器名稱：SnowLumaAdapter
- 支援的協定/API版本：OneBot V11（含 SnowLuma 扩展动作，全面兼容 NapCat，可直接連接 NapCat 後端）
- 多帳戶支援：預設多帳戶架構，支援同時配置和運行多個帳戶
- 配置鍵名：`SnowLuma_Adapter`

### 與 OneBot11 適配器的關係

SnowLuma 使用 OB11 協議，標準動作與事件轉換與 OneBot11 適配器同構（OB12 標準動作名自動映射）。
主要差異：

1. **預設 client 模式**：主動連接 SnowLuma WS（`ws://127.0.0.1:3001`），無需公網監聽
2. **bot_id 自動識別**：無需在帳戶配置中填寫 QQ 號，適配器啟動後自動探測並維護 `self_id → account_name` 映射
3. **109 個擴展動作**：拍一戳、QQ空間、群檔案/群相冊、訊息歷史、精華、已讀狀態等 SnowLuma/NapCat 兼容擴展
4. **合併轉發擴展鏈路**：專用端點 + `upload_forward_msg`（上傳節點取 resid）+ `get_forward_msg`（解析轉發內容）三級回退

## 標準 Api 動作（Api DSL）

適配器將 OneBot12 標準動作名自動映射到 OB11 動作名，模組可跨平台統一呼叫：

| OB12 標準動作 | OB11 動作 | 說明 |
|--------------|-----------|------|
| get_self_info | get_login_info | 欄位標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | 欄位標準化 |
| delete_message | delete_msg | 撤回訊息 |
| leave_group | set_group_leave | 退出群組 |
| upload_file | upload_group_file / upload_private_file | 擴展 group_id/user_id 可選參數 |

### 基本用法

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 獲取機器人資訊
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# 撤回訊息
await snowluma.Api.delete_message(message_id=123456)

# 指定帳戶（多帳戶）
result = await snowluma.Api.Using("main").get_self_info()

# 擴展動作透過 call() 逃生艙呼叫（SnowLuma/NapCat 通用）
result = await snowluma.Api.call("send_poke", group_id=123, user_id=456)
```

---

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# 使用預設帳戶發送
await snowluma.Send.To("group", group_id).Text("Hello World!")

# 指定特定帳戶發送
await snowluma.Send.Using("main").To("group", group_id).Text("來自主帳戶的消息")

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

### QQ空間

- `.QzoneMsg(content)`：發表 QQ 空間說說。
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)`：點贊/取消點贊。
- `.QzoneComment(tid, content)`：評論。
- `.QzoneDelete(tid)`：刪除。

### 群檔案 / 訊息歷史 / 已讀狀態

- `.UploadGroupFile(file, name)`：上傳群檔案（需 `To("group", group_id)`）。
- `.GetGroupFileUrl(file_id)`：取得群檔案下載連結。
- `.GetGroupMsgHistory(message_seq=0, count=20)`：取得群訊息歷史。
- `.GetFriendMsgHistory(user_id, count=20)`：取得好友訊息歷史。
- `.MarkMsgAsRead()`：標記當前會話已讀。
- `.SetOnlineStatus(status)`：設定線上狀態。

### 鏈式修飾方法（可組合使用）

- `.At(user_id: Union[str, int])`：@指定用戶（可多次調用）。
- `.AtAll()`：@全體成員。
- `.Reply(message_id: Union[str, int])`：回覆指定訊息。

## OB11 扩展動作（Api DSL）

除了標準動作外，`OB11ExtensionApi` 混入提供了 60 多個類型化的擴展方法，所有 109 個擴展動作均可透過
`Api.call("action_name", ...)` 直接呼叫（SnowLuma/NapCat 通用）。分組概覽：

| 分組 | 代表動作 |
|------|----------|
| 拍一戳 / 社交 | send_poke / group_poke / friend_poke / send_like |
| 消息回應 / 精華 | set_msg_emoji_like / get_emoji_likes / set_essence_msg / get_essence_msg_list |
| 已讀 / 狀態 | mark_msg_as_read / mark_group_msg_as_read / mark_all_as_read / set_online_status / set_input_status |
| 消息歷史 | get_group_msg_history / get_friend_msg_history |
| 群管理擴展 | set_group_reaction / set_group_remark / set_group_sign / set_group_todo / get_group_info_ex / get_group_shut_list / get_group_at_all_remain |
| 好友 / 聯絡人 | set_friend_remark / get_unidirectional_friend_list / get_friends_with_category / get_recent_contact |
| 群檔案 | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file |
| 群相簿 | get_group_album_list / get_group_album_media_list |
| QQ空間 | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds |
| 合併轉發 | get_forward_msg / upload_forward_msg |
| 媒體 / OCR | ocr_image / get_image |

## 事件類型映射

### 標準 OB12 映射

| OB11 原始類型 | 轉換後 detail_type | 說明 |
|--------------|-------------------|------|
| message_type: private | `private` | 私聊消息 |
| message_type: group | `group` | 群聊消息 |
| notice_type: group_upload | `group_file_upload` | 群文件上傳 |
| notice_type: group_admin | `group_admin_change` | 群管理員變動 |
| notice_type: group_increase | `group_member_increase` | 群成員增加 |
| notice_type: group_decrease | `group_member_decrease` | 群成員減少 |
| notice_type: group_ban | `group_ban` | 群禁言 |
| notice_type: friend_add | `friend_increase` | 好友添加 |
| notice_type: friend_delete | `friend_decrease` | 好友刪除 |
| notice_type: group_recall / friend_recall | `message_recall` | 消息撤回 |

### 平台特有事件與擴展段

- 平台特有事件（poke/honor 等）使用 `snowluma_` 前綴的 detail_type
- 未識別的 CQ 碼類型以 `onebot11_{type}` 前綴透傳（協定級前綴）
- 入站合併轉發消息段為 `onebot11_forward`（`data.id` 為 resid，可用 `Api.get_forward_msg(id=...)` 解析內容）

### 擴展字段說明

- 所有特有字段均以 `snowluma_` 前綴標識
- 保留原始事件數據在 `snowluma_raw` 字段
- 保留原始事件類型在 `snowluma_raw_type` 字段

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

| 方法 | 回傳類型 | 說明 |
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

SnowLuma 适配器採用多帳戶架構，每個帳戶獨立配置。配置鍵名為 `SnowLuma_Adapter`。

### 帳戶配置字段

| 字段 | 類型 | 必填 | 默認值 | 說明 |
|------|------|------|--------|------|
| `mode` | `str` | 否 | `"client"` | 運行模式：`"client"`（主動連接，推薦）或 `"server"`（被動監聽） |
| `url` | `str` | 否 | `"ws://127.0.0.1:3001"` | Client 模式的 WebSocket 位址（SnowLuma 預設 WS 端口 3001） |
| `token` | `str` | 否 | `""` | 訪問令牌（Bearer 認證） |
| `server_path` | `str` | 否 | `"/"` | Server 模式的 WebSocket 路徑 |
| `enabled` | `bool` | 否 | `true` | 是否啟用該帳戶 |
| `name` | `str` | 否 | `""` | 帳戶備註名稱 |

> bot_id（QQ 號）無需配置：適配器連接後自動識別，並維護 `self_id → account_name` 映射，  
> `event.reply()` 自動路由到來源帳戶。

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

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

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

### 多账户發送語法

```python
# 賬戶選擇方法
await snowluma.Send.Using("main").To("group", 123456).Text("主账户消息")

# API調用方式
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## self_id 自動映射

適配器會自動建立 OneBot `self_id`（QQ號）到 `account_name` 的映射關係，用於事件回傳路由：

```python
@message.on_message()
async def handler(event):
    # 自動路由到正確的帳戶
    await event.reply("自動路由到來源帳戶")
```