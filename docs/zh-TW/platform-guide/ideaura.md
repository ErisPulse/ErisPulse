# 花楓咖啡館（RockyChat）平台特性文件

IdeauraAdapter 是基於花楓咖啡館（RockyChat）平台 API 建構的適配器，整合了所有平台功能模組，提供統一的事件處理和訊息操作介面。

---

docs/zh-TW/quick-start.md

## 文件資訊

- 對應模組: ErisPulse-Ideaura  
- 對應模組版本: 4.0.1  
- 維護者: ErisPulse  



## 基本資訊

- 平台簡介：花楓咖啡館（RockyChat）是一個即時通訊平台
- 適配器名稱：IdeauraAdapter
- 多帳戶支援：支援透過 Bot Token 配置多個帳戶
- 鏈式修飾支援：支援 `.At()`、`.AtAll()`、`.Reply()`、`.Command()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息



## 支援的消息傳送類型

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
- `.Voice(file, filename: str = None)`：傳送語音訊息（以檔案形式傳送）。
- `.Face(face_id: str)`：傳送表情（以純文字形式傳送 emoji）。
- `.Markdown(text: str)`：傳送 Markdown 格式訊息。
- `.Html(html: str)`：傳送 HTML 格式訊息。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：編輯已有訊息。
- `.Recall(message_id: str)`：撤回訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.At(user_id: str, name: str = None)`：@指定用戶。
- `.AtAll()`：@所有人。
- `.Reply(message_id: str)`：回覆指定訊息。
- `.Command(command_id: str)`：觸發 Bot 指令，配合傳送方法使用（將訊息作為指定指令傳送）。

### 鏈式呼叫範例

```python
# 基礎傳送
await ideaura.Send.To("user", user_id).Text("Hello")

# 觸發 Bot 指令
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @用戶
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @多人
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# 回覆訊息
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回覆訊息")

# 回覆 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回覆並@")
```

### 發送到不同目標

```python
# 發送到聊天室
await ideaura.Send.To("group", "chatroom").Text("聊天室訊息")

# 發送到話題
await ideaura.Send.To("group", "topic_id").Text("話題訊息")

# 發送私聊訊息
await ideaura.Send.To("user", "user_id").Text("私聊訊息")
```

### OneBot12 訊息支援

適配器支援傳送 OneBot12 格式訊息，便於跨平台訊息相容：

- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

```python
# 發送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態
    "retcode": 0,             // 返回碼
    "data": {...},            // 响應數據
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
    - Bot指令消息段：ideaura_command
2. 擴展字段：
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

### Bot 指令消息段 (ideaura_command)

當用戶觸發 Bot 指令時，消息段類型為 `ideaura_command`：

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| 字段 | 類型 | 說明 |
|------|------|------|
| `command_id` | string | 指令 UUID |

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

## Event Mixin 擴展方法

適配器註冊了以下平台專有方法，僅在 `platform == "ideaura"` 時可用：

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_source_type()` | `str` | 消息來源類型（`chatroom`/`topic`/`private`） |
| `get_sender_name()` | `str` | 發送者暱稱 |
| `get_sender_avatar()` | `str` | 發送者頭像 URL |
| `is_sender_bot()` | `bool` | 發送者是否為機器人 |
| `is_receiver_bot()` | `bool` | 接收者是否為機器人 |
| `get_command_id()` | `str` | 觸發的 Bot 指令 ID（若有，`ideaura_command_id`） |
| `get_command()` | `str` | `get_command_id()` 的別名 |
| `get_topic_name()` | `str` | 話題名稱 |
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

## 多帳戶配置

### 配置說明

IdeauraAdapter 支援同時配置和執行多個帳戶，使用 **Bot Token** 進行驗證。

> [!WARNING]
> 從 4.0.1 版本起**移除電郵密碼登入**，僅支援 Bot Token。Bot Token 需前往 [MSCPO 開放平台](https://open.mscpo.com/rockychat/bots) 取得（以 `bot-token-` 開頭）。

```toml
# config.toml
# 帳戶1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # 機器人 API Token（必填）
enabled = true                   # 是否啟用（可選，預設為 true）

# 帳戶2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# 可選：自訂伺服器位址
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**配置項說明：**
- `token`：機器人 API Token（必填，以 `bot-token-` 開頭）
- `enabled`：是否啟用該帳戶（可選，預設為 true）

**全域配置項：**
- `base_url`：API 伺服器位址（可選，預設為 `https://api.mscpo.com/api/rockychat`）
- `ws_url`：WebSocket 伺服器位址（可選，預設為花楓咖啡館官方位址）
- `heartbeat_interval`：心跳間隔秒數（可選，預設 30 秒）

### 使用 Send DSL 指定帳戶

可以透過 `Using()` 方法指定使用哪個帳戶傳送訊息：

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# 使用帳戶名發送訊息
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# 使用 user_id 發送訊息（自動匹配對應帳戶）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 不指定時使用第一個啟用的帳戶
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### 事件中的帳戶標識

接收到的事件會自動包含對應的帳戶資訊：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"訊息來自帳戶: {account_id}")

## 擴展字段說明

- 所有特有字段均以 `ideaura_` 前綴標識，避免與標準字段衝突
- 保留原始數據在 `ideaura_raw` 字段，便於訪問平台的完整原始數據
- `self.user_id` 表示當前登錄帳戶的用戶ID
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
- 自動文件類型檢測：通過文件頭魔術字節檢測實際類型
- 智能文件名解析：對 `.bin`/`.dat`/`.tmp` 等無意義擴展名自動修正
- 支援 bytes、URL、本地路徑三種文件輸入方式
- URL 文件自動下載並上傳到伺服器

### 支援的文件類型

通過魔術字節自動檢測：

| 類型 | 擴展名 |
|------|--------|
| 圖片 | png, jpg, gif, webp |
| 視頻 | mp4, avi, flv |
| 音頻 | mp3, wav, ogg |
| 文檔 | pdf, docx |

## 注意事項

1. API 伺服器預設位址為 `https://api.mscpo.com/api/rockychat`（可透過 `base_url` 自訂）；WebSocket 位址 `wss://api-cofe.allons-y.uk:3009/mqtt` 為平台固有位址，不隨適配器名稱變更
2. 適配器使用 WebSocket 長連線接收事件，支援自動重連（固定 5 秒延遲）
3. 自身發送的消息（`isSelf: true`）會被自動過濾，不會產生事件
4. @全體（`AtAll()`）需要管理員權限
5. 檔案上傳大小限制為 10MB
6. 音訊檔案作為 `file` 子類型發送（平台不區分獨立音訊類型）
7. 表情（`Face()`）以純文字形式發送 emoji
8. 程式退出時請呼叫 `shutdown()` 確保資源釋放

