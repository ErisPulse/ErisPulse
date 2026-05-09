# 花楓咖啡館（Ideaura）平台特性文件

IdeauraAdapter 是基於花楓咖啡館（Allons）平台 API 構建的適配器，整合了所有平台功能模組，提供統一的事件處理和消息操作接口。

---

## 文件資訊

- 對應模組: ErisPulse-Ideaura
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：花楓咖啡館（Allons）是一個即時通訊平台
- 適配器名稱：IdeauraAdapter
- 多帳戶支持：支持通過 email/password 配置多個帳戶
- 鏈式修飾支持：支持 `.At()`、`.AtAll()`、`.Reply()` 等鏈式修飾方法
- OneBot12相容：支持發送 OneBot12 格式消息

## 支援的消息發送類型

所有發送方法均通過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

支持的發送類型包括：
- `.Text(text: str)`：發送純文本消息。
- `.Image(file, filename: str = None)`：發送圖片消息，支持 bytes/URL/本地路徑。
- `.Video(file, filename: str = None)`：發送視頻消息，支持 bytes/URL/本地路徑。
- `.File(file, filename: str = None)`：發送文件消息，支持 bytes/URL/本地路徑。
- `.Voice(file, filename: str = None)`：發送語音消息（作為文件發送）。
- `.Face(face_id: str)`：發送表情（以純文本形式發送 emoji）。
- `.Markdown(text: str)`：發送 Markdown 格式消息。
- `.Html(html: str)`：發送 HTML 格式消息。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：編輯已有消息。
- `.Recall(message_id: str)`：撤回消息。

### 鏈式修飾方法（可組合使用）

鏈式修飾方法返回 `self`，支持鏈式調用，必須在最終發送方法前調用：

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

### OneBot12消息支持

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
    - HTML消息段：