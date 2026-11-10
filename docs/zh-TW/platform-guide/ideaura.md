# 花楓咖啡館（RockyChat）平台特性文件

IdeauraAdapter 是基於花楓咖啡館（RockyChat）平台 API 建構的適配器，整合了所有平台功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組： ErisPulse-Ideaura
- 對應模組版本： 4.3.2
- 維護者： ErisPulse
- 最後更新： 2026-11-10

## 基本資訊

- 平台簡介：花楓咖啡館（RockyChat）是一個即時通訊平台
- 適配器名稱：IdeauraAdapter
- 多帳戶支援：支援透過 Bot Token 配置多個帳戶
- 鏈式修飾支援：支援 `.At()`、`.AtAll()`、`.Reply()`、`.Command()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 標準化對齊（4.3.2）

### 事件與帳戶

1. **事件 `self.account_id` 注入**：所有事件攜帶產生它的帳戶名，多帳戶下 `event.reply()` 自動按該帳戶受理發送
2. **帳戶配置新增 `bot_id` 可選欄位**：`IdeauraAccountConfig` 支援 `bot_id`，用於顯式指定帳戶對應的 Bot 使用者 ID
3. **好友申請事件補標準 `request_id`**：`friend_request` / `friend_event` 事件頂層新增 `request_id`（與 `ideaura_request_id` 同值），事件可用 `event.approve()` / `event.reject()` 審批

好友申請處理範例：

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_friend_request(event):
    if event.get("platform") != "ideaura":
        return
    # event["request_id"] 與 ideaura_request_id 同值
    if event.get("detail_type") == "friend":
        await event.approve()    # 同意好友申請
    # await event.reject()       # 拒絕好友申請
```

介面約定遵循 SDK 標準：[請求與審批動作規範](../standards/request-action-spec.md)。

### 動作與錯誤碼規範

1. **標準動作名不再當 HTTP 路徑轉發**：`call_api` 傳入未實作的標準動作名（如 `get_self_info`）時顯式回傳 10002，不再當作 HTTP 路徑轉發給平台；平台 HTTP 路徑呼叫需使用 `/api/` 前綴
2. 錯誤碼已標準化（原 HTTP 狀態碼、`-1`、`34000` 等舊值全部清理）：

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 33001 | 網路錯誤（請求異常、逾時等） |
| 34100 | 平台錯誤（原始回應保留在 `ideaura_raw` 欄位） |
| 10002 | 不支援的動作 / 訊息段（未實作的標準動作、Face 表情段等） |

### Send 規範

- HTML 方法名為 `HTML`（`Html` 為保留別名）
- `Face` 段回傳 10002 錯誤結果（不再降級為純文字發送），並輸出 warning 日誌
- Raw_ob12 中未知訊息段跳過並輸出 warning；全部訊息段均無法處理時回傳 10002

## v5 範式更新（4.1.0）

- **BaseConverter 繼承**：轉換器公共欄位由框架 build_base_event 建構
- **spawn_background 任務歸屬**：帳戶連線任務改用 runtime.spawn_background
- **框架軟依賴**：執行時偵測 ErisPulse>=2.7.1 並提示；啟動輸出版本日誌
- Request DSL 查詢式介面（`Request(request_id)`）暫緩；好友申請審核已可透過事件 `event.approve()` / `event.reject()` 處理（見「標準化對齊（4.3.2）」）


### 已對接平台能力

- **事件**：訊息編輯/撤回/轉發/已讀（ideaura_message_*）、好友申請（friend_request）、好友增刪（friend_increase/decrease）、線上狀態（friend_online/offline）
- **傳送**：Text / Image / Markdown / Raw_ob12（鏈式 Reply/At/AtAll 修飾）
- **好友申請審核**：4.3.2 起透過事件 `event.approve()` / `event.reject()` 支援
- **未對接**：Api DSL（平台 REST 面待開放後補充）、Request DSL 查詢式介面

---

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file, filename: str = None)`：傳送圖片訊息，支援 bytes/URL/本地路徑。
- `.Video(file, filename: str = None)`：傳送影片訊息，支援 bytes/URL/本地路徑。
- `.File(file, filename: str = None)`：傳送檔案訊息，支援 bytes/URL/本地路徑。
- `.Voice(file, filename: str = None)`：傳送語音訊息（作為檔案傳送）。
- `.Face(face_id: str)`：傳送表情（4.3.2 起**不受平台支援**，回傳 retcode=10002 並跳過，不再降級為文字）。
- `.Markdown(text: str)`：傳送 Markdown 格式訊息。
- `.HTML(html: str)`：傳送 HTML 格式訊息（`Html` 為保留別名）。
- `.MergeForward(nodes, title="合併聊天記錄")`：傳送合併轉發訊息（渲染為 `<details>` 摺疊 HTML 卡片）。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：編輯已有訊息。
- `.Recall(message_id: str)`：撤回訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法回傳 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.At(user_id: str, name: str = None)`：@指定使用者。
- `.AtAll()`：@所有人。
- `.Reply(message_id: str)`：回覆指定訊息。
- `.Command(command_id: str)`：觸發 Bot 指令，配合傳送方法使用（將訊息作為指定指令傳送）。

### 鏈式呼叫範例

```python
# 基礎傳送
await ideaura.Send.To("user", user_id).Text("Hello")

# 觸發 Bot 指令
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @使用者
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @多人
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# 回覆訊息
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回覆訊息")

# 回覆 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回覆並@")

# HTML 格式訊息
await ideaura.Send.To("group", "chatroom").HTML("<p>HTML 訊息</p>")
```

### 傳送到不同目標

```python
# 傳送到聊天室
await ideaura.Send.To("group", "chatroom").Text("聊天室訊息")

# 傳送到話題
await ideaura.Send.To("group", "topic_id").Text("話題訊息")

# 傳送私聊訊息
await ideaura.Send.To("user", "user_id").Text("私聊訊息")
```

### OneBot12訊息支援

配接器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

```python
# 傳送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

> 未知訊息段會被跳過並輸出 warning 日誌；若全部訊息段均無法處理，回傳 retcode=10002。

## 發送方法返回值

所有發送方法均返回一個 Task 物件，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 適配器標準化返回規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼（0 為成功，錯誤碼見「標準化對齊（4.3.2）」）
    "data": {...},            // 回應資料
    "self": {...},            // 自身資訊（包含 user_id）
    "message_id": "123456",   // 訊息ID
    "message": "",            // 錯誤訊息
    "ideaura_raw": {...}      // 原始回應資料
}
```

## 特有事件類型

需要 `platform=="ideaura"` 偵測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 訊息編輯：ideaura_message_edit
    - 訊息撤回：ideaura_message_recall
    - 訊息轉發：ideaura_message_forward
    - 訊息已讀：ideaura_message_read
    - 好友被拒：ideaura_friend_rejected
    - 好友上線：ideaura_friend_online
    - 好友下線：ideaura_friend_offline
    - 使用者狀態變更：ideaura_user_status_change
    - 轉發訊息段：ideaura_forwarded
    - 編輯標記段：ideaura_edited
    - Markdown訊息段：ideaura_markdown
    - HTML訊息段：ideaura_html
    - Bot指令訊息段：ideaura_command
2. 擴充欄位：
    - 所有特有欄位均以 `ideaura_` 前綴標識
    - 保留原始資料在 `ideaura_raw` 欄位
    - 事件 `self.user_id` 表示目前帳戶的使用者ID，`self.account_id` 為帳戶名

### 訊息編輯事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "訊息ID",
  "user_id": "編輯者ID",
  "ideaura_new_content": "編輯後的內容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### 訊息撤回事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "被撤回的訊息ID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回時間",
  "ideaura_is_self": false
}
```

### 訊息轉發事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "原始訊息ID",
  "user_id": "轉發者ID",
  "ideaura_forward_to": "目標話題ID",
  "ideaura_original_message_id": "原始訊息ID",
  "ideaura_forwarded_message_id": "轉發後的新訊息ID"
}
```

### 訊息已讀事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "訊息ID",
  "ideaura_reader_id": "已讀者ID",
  "ideaura_reader_name": "已讀者暱稱"
}
```

### 好友上線事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "好友ID",
  "user_nickname": "好友暱稱",
  "ideaura_friend_avatar": "頭像URL",
  "ideaura_presence_status": "online"
}
```

### 好友下線事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "好友ID",
  "ideaura_presence_status": "offline"
}
```

### 使用者狀態變更事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "使用者ID",
  "ideaura_status": "新狀態",
  "ideaura_previous_status": "舊狀態"
}
```

### 好友請求事件

4.3.2 起頂層新增標準 `request_id` 欄位（與 `ideaura_request_id` 同值），可用 `event.approve()` / `event.reject()` 審批：

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "請求者ID",
  "user_nickname": "請求者暱稱",
  "request_id": "請求ID",
  "ideaura_request_id": "請求ID",
  "ideaura_message": "驗證訊息"
}
```

### 好友被拒事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒絕者ID",
  "user_nickname": "拒絕者暱稱",
  "ideaura_request_id": "請求ID",
  "ideaura_requester_id": "請求發起者ID",
  "ideaura_requester_name": "請求發起者暱稱"
}
```

### 轉發訊息段 (ideaura_forwarded)

當收到轉發訊息時，訊息段類型為 `ideaura_forwarded`：

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `forward_source_id` | string | 轉發源訊息ID |
| `original_message_id` | string | 原始訊息ID |

### Bot 指令訊息段 (ideaura_command)

當使用者觸發 Bot 指令時，訊息段類型為 `ideaura_command`：

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| `command_id` | string | 指令 UUID |

### 事件處理範例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # 處理訊息事件
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"轉發訊息，源ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"訊息被編輯: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"訊息被撤回: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"好友上線: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"使用者狀態變更: {status}")
```

## Event Mixin 扩展方法

適配器註冊了以下平台專有方法，僅在 `platform == "ideaura"` 時可用：

| 方法 | 回傳類型 | 說明 |
|------|----------|------|
| `get_source_type()` | `str` | 消息來源類型（`chatroom`/`topic`/`private`） |
| `get_sender_name()` | `str` | 發送者暱稱 |
| `get_sender_avatar()` | `str` | 發送者頭像 URL |
| `is_sender_bot()` | `bool` | 發送者是否為機器人 |
| `is_receiver_bot()` | `bool` | 接收者是否為機器人 |
| `get_command_id()` | `str` | 觸發的 Bot 指令 ID（若有，`ideaura_command_id`） |
| `get_command()` | `str` | `get_command_id()` 的別名 |
| `get_topic_name()` | `str` | 主題名稱 |
| `get_message_type()` | `str` | 消息類型（normal/edited/forwarded/quoted） |
| `get_message_subtype()` | `str` | 消息子類型（text/image/video/file/markdown/html） |
| `is_self_message()` | `bool` | 是否為自己發送的消息 |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # 獲取觸發的 Bot 指令 ID（若有）
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"收到指令: {cmd_id}")
```

---

## 多帳戶配置

### 配置說明

IdeauraAdapter 支援同時配置和執行多個帳戶，使用 **Bot Token** 認證。

> [!WARNING]
> 4.0.1 起**移除電子郵件密碼登入**，僅支援 Bot Token。Bot Token 需前往 [MSCPO 開放平台](https://open.mscpo.com/rockychat/bots) 取得（以 `bot-token-` 開頭）。

```toml
# config.toml
# 帳戶1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # 機器人 API Token（必填）
bot_id = ""                      # Bot 使用者ID（可選，明確指定帳戶對應 Bot）
enabled = true                   # 是否啟用（可選，預設為true）

# 帳戶2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
bot_id = ""
enabled = true

# 可選：自訂伺服器位址
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**配置項說明：**
- `token`：機器人 API Token（必填，以 `bot-token-` 開頭）
- `bot_id`：Bot 使用者ID（可選，4.3.2 起支援，用於明確指定帳戶對應 Bot）
- `enabled`：是否啟用該帳戶（可選，預設為true）

**全域配置項：**
- `base_url`：API 伺服器位址（可選，預設為 `https://api.mscpo.com/api/rockychat`）
- `ws_url`：WebSocket 伺服器位址（可選，預設為花楓咖啡館官方位址）
- `heartbeat_interval`：心跳間隔秒數（可選，預設30秒）

### 使用 Send DSL 指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶傳送訊息：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# 使用帳戶名稱傳送訊息
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# 使用 user_id 傳送訊息（自動匹配對應帳戶）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 不指定時使用第一個啟用的帳戶
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### 事件中的帳戶識別

接收到的事件會自動包含對應的帳戶資訊（4.3.2 起 `self.account_id` 為帳戶名稱）：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["account_id"]
        print(f"訊息來自帳戶: {account_id}")
```

---

## 擴充欄位說明

- 所有特有欄位均以 `ideaura_` 前綴標識，避免與標準欄位衝突
- 保留原始資料在 `ideaura_raw` 欄位，便於存取平台的完整原始資料
- `self.user_id` 表示目前登入帳戶的使用者ID，`self.account_id` 為帳戶名稱
- `ideaura_source_type`：訊息來源類型（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`：發送者暱稱
- `ideaura_sender_avatar`：發送者頭像URL
- `ideaura_sender_is_bot`：發送者是否為機器人
- `ideaura_is_self`：是否為自己發送的訊息（自訊息已被過濾）
- `ideaura_topic_name`：話題名稱
- `ideaura_message_type`：訊息類型（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`：訊息子類型（text/image/video/file/markdown/html）

### 檔案處理特性

- 檔案大小限制：10MB（下載和本機讀取均有限制）
- 自動檔案類型偵測：透過檔案頭魔術位元組偵測實際類型
- 智慧檔名解析：對 `.bin`/`.dat`/`.tmp` 等無意義副檔名自動修正
- 支援 bytes、URL、本機路徑三種檔案輸入方式
- URL 檔案自動下載並上傳到伺服器

### 支援的檔案類型

透過魔術位元組自動偵測：

| 類型 | 副檔名 |
|------|--------|
| 圖片 | png, jpg, gif, webp |
| 影片 | mp4, avi, flv |
| 音訊 | mp3, wav, ogg |
| 文件 | pdf, docx |

---

## 注意事項

1. API 伺服器預設位址為 `https://api.mscpo.com/api/rockychat`（可透過 `base_url` 自訂）；WebSocket 位址 `wss://api-cofe.allons-y.uk:3009/mqtt` 為平台固有位址，不隨適配器名稱變化
2. 適配器使用 WebSocket 長連線接收事件，支援自動重新連線（固定5秒延遲）
3. 自身發送的訊息（`isSelf: true`）會被自動過濾，不會產生事件
4. @全體（`AtAll()`）需要管理員權限
5. 檔案上傳大小限制為 10MB
6. 音訊檔案作為 `file` 子類型發送（平台不區分獨立音訊類型）
7. 表情（`Face()`）不受平台支援，回傳 retcode=10002 並跳過（不再降級為純文字）
8. 程式結束時請呼叫 `shutdown()` 確保資源釋放