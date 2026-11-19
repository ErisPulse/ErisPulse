# Kook平台特性文檔

KookAdapter 是基於Kook（開黑啦）Bot WebSocket 協定建構的適配器，整合了Kook所有功能模組，提供統一的事件處理和訊息操作介面。

---

## 文檔資訊

- 對應模組版本: 4.3.2
- 維護者: ShanFish
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：Kook（原開黑啦）是一款支援文字、語音、視訊通訊的社群平台，提供完整的 Bot 開發介面
- 適配器名稱：KookAdapter
- 多帳戶支援：支援同時配置多個 Kook 機器人
- 連線方式：WebSocket 長連線（透過Kook閘道）
- 認證方式：基於 Bot Token 進行身分認證
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12相容：支援發送 OneBot12 格式訊息

## 配置說明

KookAdapter 支援多帳戶配置，每個帳戶對應一個獨立的 Kook 機器人。

```toml
# config.toml
# 帳戶1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必填，格式: Bot xxx/xxx）
bot_id = ""                   # Bot 使用者ID（可選，不填則從 token 中解析）
compress = true               # 是否啟用 WebSocket 壓縮（可選，預設為 true）
enabled = true                # 是否啟用（可選，預設為true）

# 帳戶2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> 相容舊配置：若偵測到舊的單帳戶 `[KookAdapter]` 配置（含 token），會自動遷移為 `accounts.default`。

**配置項說明（每個帳戶）：**
- `token`：Kook Bot 的 Token（必填），從 [Kook開發者中心](https://developer.kookapp.cn) 取得，格式為 `Bot xxx/xxx`
- `bot_id`：Bot 的使用者ID（可選），如果不填寫，適配器會嘗試從 token 中自動解析。建議手動填寫以確保準確性
- `compress`：是否啟用 WebSocket 資料壓縮（可選，預設為 `true`），啟用後使用 zlib 解壓縮資料
- `enabled`：是否啟用該帳戶（可選，預設為true）

**API環境：**
- Kook API 基礎位址：`https://www.kookapp.cn/api/v3`
- WebSocket 閘道透過 API 動態取得：`POST /gateway/index`

## 標準化對齊（4.3.2）

### 事件與帳戶

- **事件 `self.account_id` 注入**：所有事件攜帶產生它的帳戶名，多帳戶下 `event.reply()` 自動按該帳戶受理發送

### Api 簽名對齊

| 動作 | 簽名 | 說明 |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | 新簽名 guild_id 為首參；僅傳一個位置參數時相容舊簽名（視為 channel_id） |
| get_channel_member_list | `(guild_id, channel_id)` | 同上相容規則 |
| get_guild_info / get_guild_list | - | data 使用 `guild_id` / `guild_name` 等欄位（舊 `group_*` 欄位保留，避免破壞已有呼叫方） |

### 錯誤碼規範

錯誤碼已按 SDK 標準化，Kook 平台原始錯誤碼（401xx/4xxxx 等）不再直接作為 retcode：

| retcode | 說明 |
|---------|------|
| 0 | 成功（成功回應 `message` 為空字串） |
| 33001 | 網路錯誤（請求異常、帳戶 API 實例未初始化等） |
| 34100 | 平台錯誤（Kook 回傳非 0 code；原始回應保留在 `kook_raw`，原始 code 另存 `kook_code` 欄位） |
| 10002 | 不支援的動作（`get_guild_member_info` / `get_guild_member_list` / `set_guild_name` / `leave_guild` / `leave_channel` 顯式回傳；未知 API endpoint 不再拋出例外，統一回傳 10002） |

## v5 範式更新（4.1.0）

本適配器已完成 v5 範式對齊（增量升級，API 相容）：

- **BaseConverter 繼承**：轉換器公共欄位由框架 `build_base_event` 建構
- **Api DSL**：標準Api動作映射（見下）
- **標準 keyboard 段**：`{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` 文字+鍵盤自動組合為 Kook 卡片訊息（section + action-group）；.Keyboard(rows) 修飾器接受通用結構
- **spawn_background 任務歸屬**：連線任務改用 runtime.spawn_background
- **框架軟依賴**：執行時偵測 ErisPulse>=2.7.1 並提示；啟動輸出版本日誌

### 標準Api動作

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view（data 用 guild_id / guild_name）
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(guild_id, channel_id)  # POST /channel/view（新簽名 guild_id 為首參）
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### 按鈕（keyboard）

```python
rows = [[{"label": "選項A", "type": "callback", "data": "vote:A"},
         {"label": "官網",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("請選擇")
# 文字與按鈕自動組合為 Kook 卡片訊息（section + action-group）

# 按鈕點擊回呼（標準欄位）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---

## 支援的訊息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str)`：發送純文字訊息。
- `.Image(file: bytes | str)`：發送圖片訊息，支援檔案路徑、URL、二進位資料。
- `.Video(file: bytes | str)`：發送影片訊息，支援檔案路徑、URL、二進位資料。
- `.File(file: bytes | str, filename: str = None)`：發送檔案訊息，支援檔案路徑、URL、二進位資料。
- `.Voice(file: bytes | str)`：發送語音訊息，支援檔案路徑、URL、二進位資料。
- `.Markdown(text: str)`：發送KMarkdown格式訊息。
- `.Card(card_data: dict)`：發送卡片訊息（CardMessage）。
- `.MergeForward(nodes, title="合併聊天記錄")`：發送合併轉發訊息（渲染為卡片：標題 header + 每條訊息一個 section，KMD 跳脫，≤40 節點）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終發送方法前呼叫：

- `.Reply(message_id: str)`：回覆（引用）指定訊息。
- `.At(user_id: str)`：@指定使用者，可多次呼叫以@多個使用者。
- `.AtAll()`：@所有人。

### 鏈式呼叫範例

```python
# 基礎發送
await kook.Send.To("group", channel_id).Text("Hello")

# 回覆訊息
await kook.Send.To("group", channel_id).Reply(msg_id).Text("回覆訊息")

# @使用者
await kook.Send.To("group", channel_id).At("user_id").Text("你好")

# @多個使用者
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("多使用者@")

# @全體
await kook.Send.To("group", channel_id).AtAll().Text("公告")

# 組合使用
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合訊息")
```

### OneBot12訊息支援

適配器支援發送 OneBot12 格式的訊息，便於跨平台訊息相容：

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# 在 Raw_ob12 中使用 mention 和 reply 訊息段
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 額外操作方法

除發送訊息外，Kook適配器還支援以下操作：

```python
# 編輯訊息（僅支援 KMarkdown type=9 和 CardMessage type=10）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後的內容**")

# 撤回訊息
await kook.Send.To("group", channel_id).Recall(msg_id)

# 上傳檔案（取得檔案URL）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 發送方法回傳值

所有發送方法均回傳一個 Task 物件，可以直接 await 取得發送結果。回傳結果遵循 ErisPulse 適配器標準化回傳規範：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 回傳碼（0 為成功，平台錯誤統一 34100）
    "data": {...},            // 回應資料
    "message_id": "xxx",      // 訊息ID
    "message": "",            // 錯誤訊息（成功回應為空字串）
    "kook_raw": {...},        // 原始回應資料
    "kook_code": 0            // Kook 原始 code（錯誤時保留）
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 33001 | 網路錯誤（請求異常、帳戶 API 實例未初始化等） |
| 34100 | 平台錯誤（Kook 回傳非 0 code，原始回應保留在 `kook_raw`，原始 code 另存 `kook_code`） |
| 10002 | 不支援的動作（見「標準化對齊（4.3.2）」錯誤碼規範） |

## 特有事件類型

需要 `platform=="kook"` 偵測再使用本平台特性

### 核心差異點

1. **頻道系統**：Kook 使用伺服器（Guild）和頻道（Channel）兩層結構，頻道是訊息的基本發送目標
2. **訊息類型**：Kook 支援文字(1)、圖片(2)、影片(3)、檔案(4)、語音(8)、KMarkdown(9)、卡片訊息(10)等多種訊息類型
3. **私訊系統**：Kook 區分頻道訊息和私訊，使用不同的 API 端點
4. **訊息序號**：Kook WebSocket 使用 `sn` 序號保證訊息有序性，支援訊息暫存和亂序重排
5. **訊息編輯與撤回**：支援編輯已發送的訊息（僅 KMarkdown 和 CardMessage）和撤回訊息

### 擴充欄位

- 所有特有欄位均以 `kook_` 前綴標識
- 保留原始資料在 `kook_raw` 欄位
- `kook_raw_type` 標識原始Kook訊息類型編號（如 `1` 為文字、`255` 為通知事件）
- 事件 `self.account_id` 為產生事件的帳戶名（多帳戶下 `event.reply()` 自動按該帳戶受理）

### 特殊欄位範例

```python
# 頻道文字訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "使用者ID",
  "group_id": "頻道ID",
  "channel_id": "頻道ID",
  "message_id": "訊息ID",
  "self": {
    "platform": "kook",
    "user_id": "BotID",
    "account_id": "default"
  },
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 帶圖片的訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "使用者ID",
  "group_id": "頻道ID",
  "channel_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "圖片URL", "url": "圖片URL"}}
  ],
  "alt_message": "圖片內容"
}

# KMarkdown訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "使用者ID",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析後的純文字"}}
  ]
}

# 卡片訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "使用者ID",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "卡片JSON內容"}}
  ]
}

# 私聊訊息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "使用者ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "私聊內容"}}
  ]
}
```

### 訊息段類型

Kook 的訊息類型根據 `type` 欄位自動轉換為對應訊息段：

| Kook type | 轉換類型 | 說明 |
|---|---|---|
| 1 | `text` | 文字訊息 |
| 2 | `image` | 圖片訊息 |
| 3 | `video` | 影片訊息 |
| 4 | `file` | 檔案訊息 |
| 8 | `record` | 語音訊息 |
| 9 | `text` | KMarkdown訊息（提取純文字內容） |
| 10 | `json` | 卡片訊息（原始JSON） |

訊息段結構範例：
```json
{
  "type": "image",
  "data": {
    "file": "圖片URL",
    "url": "圖片URL"
  }
}
```

### Mention訊息段

當訊息中包含@資訊時，會在訊息段前插入 `mention` 訊息段：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@使用者ID"
  }
}
```

### mention_all訊息段

當訊息為@全體時，會插入 `mention_all` 訊息段：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket連線

### 連線流程

1. 使用 Bot Token 呼叫 `POST /gateway/index` 取得 WebSocket 閘道位址
2. 連線到 WebSocket 閘道
3. 收到 HELLO（s=1）信令，驗證連線狀態
4. 開始心跳循環（PING，s=2，每30秒一次）
5. 接收訊息事件（s=0），使用 sn 序號保證有序性
6. 收到心跳回應 PONG（s=3）

### 信令類型

| 信令 | s值 | 說明 |
|------|-----|------|
| HELLO | 1 | 伺服器歡迎信令，連線成功後收到 |
| PING | 2 | 客戶端心跳，每30秒發送一次，攜帶當前 sn |
| PONG | 3 | 心跳回應 |
| RESUME | 4 | 恢復連線信令，攜帶 sn 恢復會話 |
| RECONNECT | 5 | 伺服器要求重連，需要重新取得閘道 |
| RESUME_ACK | 6 | RESUME 成功回應 |

### 斷線重連

- 連線異常斷開後，適配器自動重試連線
- 如果之前有 `sn > 0`，會首先嘗試 RESUME（s=4）恢復連線
- RESUME 失敗後，重置 sn 和訊息佇列，重新進行全新連線（HELLO 流程）
- 收到 RECONNECT（s=5）信令時，清空狀態並重新連線

### 訊息序號機制

Kook WebSocket 使用 `sn`（遞增序號）保證訊息有序性：

- 每收到一條訊息事件（s=0），sn 遞增
- 如果收到的訊息 sn 不連續，進入暫存模式
- 暫存區中的訊息按 sn 排序，等待缺失訊息到達後按序處理
- 暫存區清空後自動退出暫存模式

## 使用範例

### 處理頻道訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### 處理私聊訊息

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"你說了: {text}")
```

### 處理通知事件（表情回應等）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"使用者 {user_id} 對訊息 {msg_id} 新增了表情回應")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"使用者 {user_id} 移除了訊息 {msg_id} 的表情回應")
```

### 發送媒體訊息

```python
# 發送圖片（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 發送圖片（二進位）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# 發送影片
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# 發送檔案
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 發送語音
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### 發送KMarkdown和卡片訊息

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**粗體** *斜體* [連結](https://example.com)")

# 卡片訊息
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "標題"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "內容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### 訊息編輯與撤回

```python
# 發送訊息
result = await kook.Send.To("group", channel_id).Markdown("**原始內容**")
msg_id = result["data"]["msg_id"]

# 編輯訊息（僅支援 KMarkdown 和 CardMessage）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後的內容**")

# 撤回訊息
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### 處理私訊的編輯和刪除通知

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"私訊已更新: {msg_id}, 新內容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"私訊已刪除: {msg_id}")
```