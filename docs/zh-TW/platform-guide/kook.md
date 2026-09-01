# Kook 平台特性文件

KookAdapter 是基於 Kook（開黑啦）Bot WebSocket 協議建構的適配器，整合了 Kook 所有功能模組，提供統一的事件處理和訊息操作介面。

---

## 文件資訊

- 對應模組版本: 0.1.0
- 維護者: ShanFish

## 基本資訊

- 平台簡介：Kook（原開黑啦）是一款支援文字、語音、視訊通訊的社群平台，提供完整的 Bot 開發介面
- 适配器名称：KookAdapter
- 多賬戶支援：支援同時配置多個 Kook 機器人
- 連接方式：WebSocket 長連接（通過 Kook 網關）
- 認證方式：基於 Bot Token 進行身份認證
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12 兼容：支援發送 OneBot12 格式訊息

## 配置說明

KookAdapter 支援多帳戶配置，每個帳戶對應一個獨立的 Kook 机器人工。

```toml
# config.toml
# 帳戶1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必填，格式: Bot xxx/xxx）
bot_id = ""                   # Bot 用戶ID（可選，不填則從 token 中解析）
compress = true               # 是否啟用 WebSocket 壓縮（可選，預設為 true）
enabled = true                # 是否啟用（可選，預設為true）

# 帳戶2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> 兼容舊配置：若檢測到舊的單帳戶 `[KookAdapter]` 配置（含 token），會自動遷移為 `accounts.default`。

**配置項說明（每個帳戶）：**
- `token`：Kook Bot 的 Token（必填），從 [Kook開發者中心](https://developer.kookapp.cn) 獲取，格式為 `Bot xxx/xxx`
- `bot_id`：Bot 的用戶ID（可選），如果不填寫，適配器會嘗試從 token 中自動解析。建議手動填寫以確保準確性
- `compress`：是否啟用 WebSocket 數據壓縮（可選，預設為 `true`），啟用後使用 zlib 解壓數據
- `enabled`：是否啟用該帳戶（可選，預設為true）

**API環境：**
- Kook API 基礎地址：`https://www.kookapp.cn/api/v3`
- WebSocket 網關透過 API 動態獲取：`POST /gateway/index`

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支援的傳送類型包括：
- `.Text(text: str)`：傳送純文字訊息。
- `.Image(file: bytes | str)`：傳送圖片訊息，支援檔案路徑、URL、二進位資料。
- `.Video(file: bytes | str)`：傳送影片訊息，支援檔案路徑、URL、二進位資料。
- `.File(file: bytes | str, filename: str = None)`：傳送檔案訊息，支援檔案路徑、URL、二進位資料。
- `.Voice(file: bytes | str)`：傳送語音訊息，支援檔案路徑、URL、二進位資料。
- `.Markdown(text: str)`：傳送KMarkdown格式訊息。
- `.Card(card_data: dict)`：傳送卡片訊息（CardMessage）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：傳送 OneBot12 格式訊息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支援鏈式呼叫，必須在最終傳送方法前呼叫：

- `.Reply(message_id: str)`：回覆（引用）指定訊息。
- `.At(user_id: str)`：@指定使用者，可多次呼叫以@多個使用者。
- `.AtAll()`：@所有人。

### 鏈式呼叫範例

```python
# 基礎傳送
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

適配器支援傳送 OneBot12 格式的訊息，便於跨平台訊息相容：

```python
# 傳送 OneBot12 格式訊息
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 配合鏈式修飾
ob12_msg = [{"type": "text", "data": {"text": "回覆訊息"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# 在 Raw_ob12 中使用 mention 和 reply 消息段
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 額外操作方法

除了傳送訊息外，Kook 適配器還支援以下操作：

```python
# 編輯訊息（僅支援 KMarkdown type=9 和 CardMessage type=10）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後的內容**")

# 撤回訊息
await kook.Send.To("group", channel_id).Recall(msg_id)

# 上傳檔案（取得檔案URL）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 發送方法返回值

所有發送方法均返回一個 Task 對象，可以直接 await 獲取發送結果。返回結果遵循 ErisPulse 适配器标准化返回规范：

```python
{
    "status": "ok",           // 執行狀態: "ok" 或 "failed"
    "retcode": 0,             // 返回碼（Kook API 的 code）
    "data": {...},            // 响应数据
    "message_id": "xxx",      // 消息ID
    "message": "",            // 錯誤信息
    "kook_raw": {...}         // 原始響應數據
}
```

### 錯誤碼說明

| retcode | 說明 |
|---------|------|
| 0 | 成功 |
| 40100 | Token 無效或未提供 |
| 40101 | Token 過期 |
| 40102 | Token 與 Bot 不匹配 |
| 40103 | 缺少權限 |
| 40000 | 參數錯誤 |
| 40400 | 目標不存在 |
| 40300 | 無權限操作 |
| 50000 | 伺服器內部錯誤 |
| -1 | 适配器內部錯誤 |

## 特有事件類型

需要 `platform=="kook"` 檢測再使用本平台特性

### 核心差異點

1. **頻道系統**：Kook 使用伺服器（Guild）和頻道（Channel）兩層結構，頻道是訊息的基本發送目標
2. **訊息類型**：Kook 支援文本(1)、圖片(2)、影片(3)、檔案(4)、語音(8)、KMarkdown(9)、卡片訊息(10)等多種訊息類型
3. **私信系統**：Kook 區分頻道訊息和私信訊息，使用不同的 API 端點
4. **訊息序號**：Kook WebSocket 使用 `sn` 序號保證訊息有序性，支援訊息暫存和亂序重排
5. **訊息編輯與撤回**：支援編輯已發送的訊息（僅 KMarkdown 和 CardMessage）和撤回訊息

### 擴展欄位

- 所有特有欄位均以 `kook_` 前綴標識
- 保留原始資料在 `kook_raw` 欄位
- `kook_raw_type` 標識原始 Kook 訊息類型編號（如 `1` 為文本、`255` 為通知事件）

### 特殊欄位範例

```python
# 頻道文本訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "channel_id": "頻道ID",
  "message_id": "訊息ID",
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
  "user_id": "用戶ID",
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
  "user_id": "用戶ID",
  "group_id": "頻道ID",
  "message_id": "訊息ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析後的純文本"}}
  ]
}

# 卡片訊息
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用戶ID",
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
  "user_id": "用戶ID",
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
| 1 | `text` | 文本訊息 |
| 2 | `image` | 圖片訊息 |
| 3 | `video` | 影片訊息 |
| 4 | `file` | 檔案訊息 |
| 8 | `record` | 語音訊息 |
| 9 | `text` | KMarkdown訊息（提取純文本內容） |
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
    "user_id": "被@用戶ID"
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

## WebSocket 連接

### 連接流程

1. 使用 Bot Token 調用 `POST /gateway/index` 以獲取 WebSocket 網關地址
2. 連接到 WebSocket 網關
3. 收到 HELLO（s=1）信令，驗證連接狀態
4. 開始心跳循環（PING，s=2，每 30 秒一次）
5. 接收消息事件（s=0），使用 sn 序號以確保有序性
6. 收到心跳響應 PONG（s=3）

### 信令類型

| 信令 | s 值 | 說明 |
|------|-----|------|
| HELLO | 1 | 伺服器歡迎信令，連接成功後收到 |
| PING | 2 | 客戶端心跳，每 30 秒發送一次，攜帶當前 sn |
| PONG | 3 | 心跳響應 |
| RESUME | 4 | 恢復連接信令，攜帶 sn 以恢復會話 |
| RECONNECT | 5 | 伺服器要求重連，需要重新獲取網關 |
| RESUME_ACK | 6 | RESUME 成功響應 |

### 斷線重連

- 連接異常斷開後，適配器自動重試連接
- 如果之前有 `sn > 0`，會首先嘗試 RESUME（s=4）以恢復連接
- RESUME 失敗後，重置 sn 和訊息佇列，重新進行全新連接（HELLO 流程）
- 收到 RECONNECT（s=5）信令時，清除狀態並重新連接

### 消息序號機制

Kook WebSocket 使用 `sn`（遞增序號）以確保訊息有序性：

- 每收到一條訊息事件（s=0），sn 會遞增
- 如果收到的訊息 sn 不連續，則進入暫存模式
- 暫存區中的訊息按 sn 排序，等待缺失訊息到達後按序處理
- 暫存區清空後自動退出暫存模式

## 使用示例

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
        print(f"用戶 {user_id} 對訊息 {msg_id} 添加了表情回應")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用戶 {user_id} 移除了訊息 {msg_id} 的表情回應")
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

### 處理私訊訊息的編輯和刪除通知

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"私訊訊息已更新: {msg_id}, 新內容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"私訊訊息已刪除: {msg_id}")
```