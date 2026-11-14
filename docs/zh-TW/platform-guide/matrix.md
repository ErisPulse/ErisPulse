# Matrix平台特性文件

MatrixAdapter 是基於 [Matrix協議](https://spec.matrix.org/) 建構的適配器，整合了 Matrix 協議的所有核心功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 4.6.1
- 維護者: ErisPulse
- 最後更新: 2026-11-10

## 基本資訊

- 平台簡介：Matrix 是一個開放的去中心化通訊協議，支援私聊、群組等多種場景
- 適配器名稱：MatrixAdapter
- 多帳號支援：支援同時配置多個 Matrix 帳號
- 連接方式：Long Polling（透過 Matrix Sync API `/sync`）
- 認證方式：基於 access_token 或 user_id + password 登入獲取 token
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 配置說明

MatrixAdapter 支援多帳戶配置，每個帳戶獨立配置 homeserver 和認證資訊。

```toml
# config.toml
# 帳戶1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrix 伺服器地址（必填）
access_token = "YOUR_ACCESS_TOKEN"          # 訪問令牌（與 user_id+password 二選一）
user_id = ""                                # Matrix 用戶 ID（如 @bot:matrix.org）
password = ""                               # Matrix 用戶密碼
auto_accept_invites = true                  # 是否自動接受房間邀請（可選，預設為 true）
enabled = true                              # 是否啟用（可選，預設為 true）

# 帳戶2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 兼容舊配置：若檢測到舊的單帳戶 `[Matrix_Adapter]` 配置（含 access_token），會自動遷移為 `accounts.default`。

**配置項說明（每個帳戶）：**
- `homeserver`：Matrix 伺服器地址（必填），預設為 `https://matrix.org`
- `access_token`：訪問令牌，可從 Matrix 客戶端獲取。如果已有 token，直接填寫即可
- `user_id`：Matrix 用戶 ID（如 `@bot:matrix.org`），與 `password` 配合使用進行登入
- `password`：Matrix 用戶密碼，用於自動登入獲取 access_token
- `auto_accept_invites`：是否自動接受房間邀請，預設為 `true`
- `enabled`：是否啟用該帳戶（可選，預設為 true）
- `encryption_enabled`：是否啟用端到端加密，預設為 `false`
- `trust_all_devices`：是否自動信任未驗證裝置（E2EE），預設為 `true`
- `device_id`：裝置 ID（E2EE，通常自動獲取，無需填寫）
- `store_path`：加密會話儲存目錄（E2EE），預設為 `data/matrix/<帳戶名>`

**認證方式：**
- 方式一（推薦）：直接提供 `access_token`
- 方式二：提供 `user_id` 和 `password`，適配器會自動呼叫登入介面獲取 token

## v5 範式更新（4.2.0）

- **BaseConverter 繼承**：轉換器公共欄位由框架 build_base_event 建構
- **Api DSL**：get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + 元動作
- **訊息事件補充 message_id**（event_id）；訊息登記表支援 delete_message
- **spawn_background 任務歸屬**：同步/心跳任務改用 runtime.spawn_background
- **框架軟依賴**：運行時檢測 ErisPulse>=2.7.1 並提示；啟動輸出版本日誌
- Matrix 無原生按鈕能力，標準 keyboard 段優雅忽略（不報錯）

## 端到端加密（4.3.0）

4.3.0 起適配器原生支援加密房間的端到端加密（基於 matrix-nio[e2e] / vodozemac）：

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # 啟用（預設 false，存量部署不受影響）
trust_all_devices = true        # 自動信任未驗證裝置（預設；false 為嚴格模式）
```

- 加密房間訊息收發自動解密/加密，媒體端到端加密（`m.file.encrypted`）
- `device_id` 自動解析與持久化；會話儲存於 `store_path`（預設 `data/matrix/<帳號名>`，**請勿刪除**，否則歷史訊息無法解密）
- 事件 Mixin 新增 `event.is_encrypted()`；媒體段攜帶 `matrix_encrypted_file`（JWK），可用 `MatrixAdapter.decrypt_media()` 解密
- 不支援交叉簽名與伺服器端密鑰備份；需要 Python >= 3.10
- 未啟用或未安裝 matrix-nio 時自動降級為明文模式

詳細說明見下文[端到端加密（E2EE）](#端到端加密e2ee)章節與[適配器 README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter)。

## 標準化對齊

本節說明適配器與 ErisPulse 標準化規範對齊的行為。規範詳情參見 SDK 文件《API 回應規範》（`docs/zh-TW/standards/api-response.md`）與《發送方法規範》（`docs/zh-TW/standards/send-method-spec.md`）。

### 多帳戶受理（4.6.1 起）

- 所有事件注入 `self.account_id`（來源帳戶名）；access_token 登入帳戶在 `user_id` 為空時也能正確完成多帳戶受理與事件回路由

### 錯誤碼規範化（4.6.x）

- **媒體上傳/下載失敗與請求超時統一 33001**（網路錯誤）
- **平台 API 失敗統一 34100**（平台錯誤），Matrix errcode 保留在 `message` 與 `matrix_raw` 欄位
- **撤回上下文缺失 10003**：`delete_message` 未找到訊息歸屬上下文時返回參數錯誤

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 10002 | 不支援的動作（如 get_friend_list，Matrix 無好友概念） |
| 10003 | 發送目標無效（無法解析為 Matrix 房間）、撤回上下文缺失 |
| 33001 | 網路錯誤（媒體上傳/下載失敗、請求超時） |
| 34100 | 平台 API 失敗（Matrix errcode 保留在 message 與 matrix_raw） |

### Send 規範

- Send 全方法讀取 `send_context`：事件鏈內自動使用當前事件來源帳戶，顯式 `Using()` 指定的帳戶優先
- HTML 方法：`.Html(html, fallback)` 發送富文本訊息；`HTML` 為規範拼寫別名（`Html` 保留相容既有模組）
- `get_group_list` 返回每項補齊 `group_name` 欄位（與 `get_group_info` 一致）

### 標準 Api 動作示例

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms（每項含 group_name）
await matrix.Api.delete_message(event_id)            # redact（登記表補全 room_id）
```

---

### 已對接平台能力

- **事件**：訊息（m.room.message：文本/圖片/文件/音視頻/回覆/編輯）、成員增減（m.room.member）、房間名稱變更等狀態事件
- **會話**：私聊（DM 房間自動發現）/ 群組（房間）；發送支援 Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**：whoami/profile/joined_rooms/房間狀態/成員列表/leave/redact（見上方 Api DSL）

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實作，例如：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file: bytes | str)`：傳送圖片訊息，支援檔案路徑、URL、MXC URI、二進制資料。
- `.Voice(file: bytes | str)`：傳送語音訊息，支援檔案路徑、URL、MXC URI、二進制資料。
- `.Video(file: bytes | str)`：傳送影片訊息，支援檔案路徑、URL、MXC URI、二進制資料。
- `.File(file: bytes | str, filename: str = "")`：傳送檔案訊息，支援檔案路徑、URL、MXC URI、二進制資料。
- `.Notice(text: str)`：傳送通知訊息（Matrix 的 m.notice 類型）。
- `.Html(html: str, fallback: str = "")`：傳送 HTML 格式訊息，支援富文本內容（`HTML` 為規範拼寫別名）。
- `.MergeForward(nodes, title="合併聊天記錄")`：傳送合併轉發訊息（formatted_body blockquote 引用塊形態；白名單會剝離 details/內聯樣式）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆指定訊息（透過 Matrix `m.in_reply_to` 關係）。
- `.At(user_id: str)`：@指定用戶（透過 Matrix `m.mentions` 字段實作）。
- `.AtAll()`：@房間內所有人（透過 Matrix `@room` 提及實作）。

### 鏈式呼叫示例

```python
# 基礎傳送（"user" 目標支援用戶 ID（@user:server，自動反查 DM 房間）或房間 ID（!room:server））
await matrix.Send.To("user", "@alice:matrix.org").Text("Hello")

# 回覆訊息
await matrix.Send.To("group", room_id).Reply("$event_id").Text("回覆訊息")

# @用戶
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("你好")

# @所有人
await matrix.Send.To("group", room_id).AtAll().Text("公告通知")

# 組合使用：回覆 + @
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合訊息")

# 發送 HTML 訊息
await matrix.Send.To("group", room_id).Html("<h1>標題</h1><p>內容</p>", fallback="標題\n內容")

# 發送通知訊息
await matrix.Send.To("group", room_id).Notice("系統通知")
```

### OneBot12 訊息支援

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雜訊息
ob12_msg = [
    {"type": "text", "data": {"text": "看這張圖片："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "不錯吧？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

# 位置訊息（標準 location 段 → Matrix m.location；與文字共存時拆分為獨立事件）
ob12_msg = [
    {"type": "text", "data": {"text": "我在這裡"}},
    {"type": "location", "data": {"latitude": 39.9, "longitude": 116.4, "title": "北京市"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼
    "data": {...},            // 响應數據
    "message_id": "$event_id", // Matrix事件ID
    "message": "",            // 錯誤信息
    "matrix_raw": {...}       // 原始響應數據
}
```

錯誤碼規範見上文[標準化對齊](#標準化對齊)章節。

## 特有事件類型

需要 `platform=="matrix"` 檢測再使用本平台特性

### 核心差異點

1. **去中心化架構**：Matrix 是一個去中心化的通信協議，使用者ID格式為 `@user:server.domain`，房間ID格式為 `!room_id:server.domain`
2. **房間概念**：Matrix 不區分群聊和私聊，所有對話都是「房間」。適配器透過 DM（Direct Message）帳戶資料自動識別私聊房間
3. **Long Polling 同步**：使用 `/sync` API 進行長輪詢以獲取新事件，而非 WebSocket
4. **MXC URI**：媒體檔案透過 `mxc://server.domain/media_id` 格式引用
5. **HTML 富文本**：支援透過 `formatted_body` 發送 HTML 格式訊息
6. **表情回應**：支援訊息層級的表情回應（Reaction），有別於傳統的回覆訊息
7. **訊息編輯**：支援透過 `m.replace` 關係編輯已發送的訊息
8. **訊息撤回**：支援透過 `m.room.redaction` 撤回/刪除訊息

### 擴展欄位

- 所有特有欄位均以 `matrix_` 前綴標識
- 保留原始資料在 `matrix_raw` 欄位
- `matrix_raw_type` 標識原始Matrix事件類型（如 `m.room.message`、`m.room.member`）

### 特殊欄位範例

```python
# 群組訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# 私聊訊息
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 表情回應
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# 訊息撤回
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# 訊息編輯
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": True,
  "matrix_original_event_id": "$original_event_id"
}

# 線程訊息
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### 訊息段類型

Matrix訊息根據 `msgtype` 自動轉換為對應的訊息段：

| msgtype | 轉換類型 | 說明 |
|---|---|---|
| m.text | `text` | 文本訊息 |
| m.notice | `text` | 通知訊息 |
| m.emote | `text` | 動作訊息 |
| m.image | `image` | 圖片訊息 |
| m.audio | `audio` | 音訊訊息（標準訊息段名為 `audio`；`voice` 是發送方法名，不是段名） |
| m.video | `video` | 影片訊息 |
| m.file | `file` | 檔案訊息 |
| m.location | `location` | 位置訊息（latitude/longitude 由 geo URI 解析） |

> 提及（mention）：訊息 content 中的 `m.mentions`（Matrix v1.11+ 規範）會轉換為標準 `mention` 段——
> `m.mentions.user_ids` → `mention(user_id=...)`，`m.mentions.room` → `mention(user_id="all")`。

訊息段結構範例：

```json
// 文本訊息（帶HTML）
{
  "type": "text",
  "data": {
    "text": "純文本內容",
    "html": "<b>HTML內容</b>"
  }
}

// 圖片訊息
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置訊息（latitude/longitude 從 geo URI 解析）
{
  "type": "location",
  "data": {
    "latitude": 39.9,
    "longitude": 116.4,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin 方法

MatrixAdapter 註冊了以下事件混入方法，可在事件處理中直接調用：

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_room_id()` | `str` | 獲取房間ID |
| `get_matrix_event_type()` | `str` | 獲取原始Matrix事件類型 |
| `get_matrix_sender()` | `str` | 獲取原始發送者ID |
| `get_reaction_key()` | `str` | 獲取回應表情 |
| `is_edited()` | `bool` | 判斷訊息是否為編輯訊息 |
| `is_notice()` | `bool` | 判斷訊息是否為 m.notice 類型 |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API 連接

### 同步流程

1. 使用 access_token 或 user_id + password 進行認證
2. 呼叫 `/_matrix/client/v3/account/whoami` 獲取 bot_user_id
3. 發出 connect 元事件
4. 執行初始同步（`/_matrix/client/v3/sync?timeout=0`）獲取 `next_batch` token
5. 發現 DM 房間（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. 開始 Long Polling 同步迴圈（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 處理每次同步回傳的新事件並轉換發出

### 心跳機制

- 適配器每 30 秒發出一次 `heartbeat` 元事件
- 連接成功時發出 `connect` 元事件
- 關閉時發出 `disconnect` 元事件

### 房間邀請

- 收到房間邀請（`invite` 狀態的房間）時，如果 `auto_accept_invites` 配置為 `true`（預設），適配器會自動加入房間
- 加入房間呼叫 `/_matrix/client/v3/join/{room_id}` 接口

## 端到端加密（E2EE）

適配器自 4.3.0 起原生支援加密房間的端到端加密（基於 matrix-nio[e2e] / vodozemac），`encryption_enabled = true` 啟用。

### 工作機制

- **同步**：啟用後同步走 nio E2EE 會話，裝置密鑰上傳、一次性密鑰補充、to-device 消息（Olm/Megolm 會話密鑰分發）全部自動處理；timeline 中的 `m.room.encrypted` 事件自動解密為明文事件再走統一轉換
- **發送**：目標房間為加密房間時自動分享 Megolm 會話並加密載荷；解密失敗的事件跳過並記錄警告
- **媒體**：加密房間中的媒體上傳為端到端加密（`m.file.encrypted`）；接收端媒體段攜帶 `matrix_encrypted_file`（JWK，含 url/key/iv/hashes），下載密文後可透過 `MatrixAdapter.decrypt_media(ciphertext, key, iv, sha256)` 解密
- **裝置**：`device_id` 自動解析（登入回應 → `/whoami` → 本地持久化），密碼重登復用同一裝置；`trust_all_devices = true`（預設）自動信任未驗證裝置（bot 場景慣例），`false` 為嚴格模式
- **降級**：E2EE 未啟用或 matrix-nio 未安裝時自動回退明文 REST 路徑，行為與舊版完全一致

### 模組側介面

- 事件 Mixin：`event.is_encrypted()` 判斷訊息是否來自加密房間
- 媒體段標記：`encrypted: true` 與 `matrix_encrypted_file`（JWK）
- 解密輔助：`MatrixAdapter.decrypt_media(file_bytes, key, iv, hash_value) -> bytes`

### 已知限制

- 不支援交叉簽名（cross-signing）與伺服器端密鑰備份（room key backup）
- 本地會話儲存目錄（`store_path`，預設 `data/matrix/<帳號名>`）刪除後歷史訊息無法解密
- 互動式 SAS（emoji）驗證暫未支援，計畫後續版本提供

## 使用示例

### 處理群組訊息

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 處理表情回應

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 處理表情回應...
```

### 發送媒體訊息

```python
# 發送圖片（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 發送圖片（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 發送圖片（二進制數據）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 發送圖片（本地檔案路徑）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# 發送檔案（附檔名）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="文件.pdf")
```

### 處理訊息編輯

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 處理編輯訊息...
```

### 監聽成員變更

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"使用者 {nickname} ({user_id}) 加入了房間")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"使用者 {user_id} 被移除，操作者: {operator_id}")
```