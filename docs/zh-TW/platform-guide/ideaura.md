# 花楓咖啡館（Ideaura）平台特性文件

IdeauraAdapter 是基於花楓咖啡館（Allons）平台 API 構建的適配器，整合了所有平台功能模組，提供統一的事件處理和消息操作接口。

---

## 文件資訊

- 對應模組: ErisPulse-Ideaura
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：花楓咖啡館（Allons）是一個即時通訊平台
- 适配器名稱：IdeauraAdapter
- 多帳戶支持：支援透過 token 或 email/password 配置多個帳戶
- 鏈式修飾支持：支援 `.At()`、`.AtAll()`、`.Reply()` 等鏈式修飾方法
- OneBot12相容：支援發送 OneBot12 格式消息

## 支援的消息發送類型

所有發送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

支援的發送類型包括：
- `.Text(text: str)`：發送純文本消息。
- `.Image(file, filename: str = None)`：發送圖片消息，支援 bytes/URL/本地路徑。
- `.Video(file, filename: str = None)`：發送視頻消息，支援 bytes/URL/本地路徑。
- `.File(file, filename: str = None)`：發送文件消息，支援 bytes/URL/本地路徑。
- `.Voice(file, filename: str = None)`：發送語音消息（作為文件發送）。
- `.Face(face_id: str)`：發送表情（以純文本形式發送 emoji）。
- `.Markdown(text: str)`：發送 Markdown 格式消息。
- `.Html(html: str)`：發送 HTML 格式消息。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：編輯已有消息。
- `.Recall(message_id: str)`：撤回消息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式調用，必須在最終發送方法前調用：

- `.At(user_id: str, name: str = None)`：@指定用戶。
- `.AtAll()`：@所有人。
- `.Reply(message_id: str)`：回覆指定消息。

### 鏈式調用示例

```python
# 基礎發送
await ideaura.Send.To("user", user_id).Text("Hello")

# @用戶
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @多人
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# 回覆消息
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回覆消息")

# 回覆 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回覆並@")
```

### 發送到不同目標

```python
# 發送到聊天室
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# 發送到話題
await ideaura.Send.To("group", "topic_id").Text("話題消息")

# 發送私聊消息
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### OneBot12消息支援

適配器支援發送 OneBot12 格式的消息，便於跨平台消息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：發送 OneBot12 格式消息。

```python
# 發送 OneBot12 格式消息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 適配器標準化返回規範：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 響應數據
    "self": {...},            // 自身信息（包含 user_id）
    "message_id": "123456",   // 消息ID
    "message": "",            // 錯誤信息
    "ideaura_raw": {...}      // 原始響應數據
}
```

## 特有事件類型

需要 `platform=="ideaura"` 檢測再使用本平台特性

### 核心差異點

1. 特有事件類型：
    - 消息編輯：ideaura_message_edit
    - 消息撤回：ideaura_message_recall
    - 消息轉發：ideaura_message_forward
    - 消息已讀：ideaura_message_read
    - 好友被拒：ideaura_friend_rejected
    - 好友上線：ideaura_friend_online
    - 好友下線：ideaura_friend_offline
    - 用戶狀態變更：ideaura_user_status_change
    - 轉發消息段：ideaura_forwarded
    - 編輯標記段：ideaura_edited
    - Markdown消息段：ideaura_markdown
    - HTML消息段：ideaura_html
2. 扩展字段：
    - 所有特有字段均以 `ideaura_` 前綴標識
    - 保留原始數據在 `ideaura_raw` 字段
    - `self.user_id` 表示當前帳戶的用戶ID

### 消息編輯事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "消息ID",
  "user_id": "編輯者ID",
  "ideaura_new_content": "編輯後的內容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### 消息撤回事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "被撤回的消息ID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回時間",
  "ideaura_is_self": false
}
```

### 消息轉發事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "原始消息ID",
  "user_id": "轉發者ID",
  "ideaura_forward_to": "目標話題ID",
  "ideaura_original_message_id": "原始消息ID",
  "ideaura_forwarded_message_id": "轉發後的新消息ID"
}
```

### 消息已讀事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "消息ID",
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

### 用戶狀態變更事件

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "用戶ID",
  "ideaura_status": "新狀態",
  "ideaura_previous_status": "舊狀態"
}
```

### 好友請求事件

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "請求者ID",
  "user_nickname": "請求者暱稱",
  "ideaura_request_id": "請求ID",
  "ideaura_message": "驗證消息"
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

### 轉發消息段 (ideaura_forwarded)

當收到轉發消息時，消息段類型為 `ideaura_forwarded`：

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `forward_source_id` | string | 轉發源消息ID |
| `original_message_id` | string | 原始消息ID |

### 事件處理示例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # 處理消息事件
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"轉發消息，源ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"消息被編輯: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"消息被撤回: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"好友上線: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"用戶狀態變更: {status}")
```

---

## 多帳戶配置

### 配置說明

IdeauraAdapter 支援同時配置和運行多個帳戶，每個帳戶可選擇 Token 登入或郵箱密碼登入（二選一）。

```toml
# config.toml
# 帳戶1：Token 登入（推薦，無需郵箱密碼）
[IdeauraAdapter.accounts.default]
token = "your-token-here"        # 登入Token（與 email+password 二選一）
enabled = true                   # 是否啟用（可選，預設為true）

# 帳戶2：郵箱密碼登入
[IdeauraAdapter.accounts.bot2]
email = "user2@example.com"      # 登入郵箱
password = "password2"           # 登入密碼
enabled = true

# 可選：自定義伺服器地址
[IdeauraAdapter]
base_url = "https://api-cofe.allons-y.uk:3009"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**配置項說明：**
- `token`：登入Token（選填，填寫後優先使用Token登入，無需郵箱密碼）
- `email`：登入郵箱（Token登入時可不填，郵箱密碼登入時必填）
- `password`：登入密碼（Token登入時可不填，郵箱密碼登入時必填）
- `enabled`：是否啟用該帳戶（可選，預設為true）

**全域配置項：**
- `base_url`：API 伺服器地址（可選，預設為花楓咖啡館官方地址）
- `ws_url`：WebSocket 伺服器地址（可選，預設為花楓咖啡館官方地址）
- `heartbeat_interval`：心跳間隔秒數（可選，預設30秒）

### 使用 Send DSL 指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶發送消息：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# 使用帳戶名發送消息
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# 使用 user_id 發送消息（自動匹配對應帳戶）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 不指定時使用第一個啟用的帳戶
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### 事件中的帳戶標識

接收到的事件會自動包含對應的帳戶信息：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"消息來自帳戶: {account_id}")
```

---

## 扩展字段說明

- 所有特有字段均以 `ideaura_` 前綴標識，避免與標準字段衝突
- 保留原始數據在 `ideaura_raw` 字段，便於訪問平台的完整原始數據
- `self.user_id` 表示當前登入帳戶的用戶ID
- `ideaura_source_type`：消息來源類型（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`：發送者暱稱
- `ideaura_sender_avatar`：發送者頭像URL
- `ideaura_sender_is_bot`：發送者是否為機器人
- `ideaura_is_self`：是否為自己發送的消息（自消息已被過濾）
- `ideaura_topic_name`：話題名稱
- `ideaura_message_type`：消息類型（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`：消息子類型（text/image/video/file/markdown/html）

### 文件處理特性

- 文件大小限制：10MB（下載和本地讀取均有限制）
- 自動文件類型檢測：透過文件頭魔法字節檢測實際類型
- 智能文件名解析：對 `.bin`/`.dat`/`.tmp` 等無意義擴展名自動修正
- 支援 bytes、URL、本地路徑三種文件輸入方式
- URL 文件自動下載並上傳到伺服器

### 支援的文件類型

透過魔法字節自動檢測：

| 類型 | 擴展名 |
|------|--------|
| 圖片 | png, jpg, gif, webp |
| 視頻 | mp4, avi, flv |
| 音頻 | mp3, wav, ogg |
| 文檔 | pdf, docx |

---

## 注意事項

1. 伺服器地址 `api-cofe.allons-y.uk` 是平台固有地址，不隨適配器名稱變化
2. 適配器使用 WebSocket 長連接接收事件，支援自動重連（固定5秒延遲）
3. 自身發送的消息（`isSelf: true`）會被自動過濾，不會產生事件
4. @全體（`AtAll()`）需要管理員權限
5. 文件上傳大小限制為 10MB
6. 音頻文件作為 `file` 子類型發送（平台不區分獨立音頻類型）
7. 表情（`Face()`）以純文本形式發送 emoji
8. 程序退出時請調用 `shutdown()` 確保資源釋放