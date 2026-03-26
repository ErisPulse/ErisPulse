# Telegram 平台特性文件

TelegramAdapter 是基於 Telegram Bot API 建立的適配器，支援多種訊息類型與事件處理。

---

## 文件資訊

- 對應模組版本: 3.5.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：Telegram 是一個跨平台的即時通訊軟體
- 適配器名稱：TelegramAdapter
- 支援的協定/API版本：Telegram Bot API

## 支援的訊息傳送類型

所有傳送方法均透過鏈式語法實現，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本傳送方法

- `.Text(text: str)`：傳送純文字訊息。
- `.Face(emoji: str)`：傳送表情訊息。
- `.Markdown(text: str, content_type: str = "MarkdownV2")`：傳送 Markdown 格式訊息。
- `.HTML(text: str)`：傳送 HTML 格式訊息。

### 媒體傳送方法

所有媒體方法支援兩種輸入方式：
- **URL 方式**：直接傳入字串 URL
- **檔案上傳**：傳入 bytes 類型資料

- `.Image(file: bytes | str, caption: str = "", content_type: str = None)`：傳送圖片訊息
- `.Video(file: bytes | str, caption: str = "", content_type: str = None)`：傳送影片訊息
- `.Voice(file: bytes | str, caption: str = "")`：傳送語音訊息
- `.Audio(file: bytes | str, caption: str = "", content_type: str = None)`：傳送音訊訊息
- `.File(file: bytes | str, caption: str = "")`：傳送檔案訊息
- `.Document(file: bytes | str, caption: str = "", content_type: str = None)`：傳送文件訊息

### 訊息管理方法

- `.Edit(message_id: int, text: str, content_type: str = None)`：編輯既有訊息。
- `.Recall(message_id: int)`：刪除指定訊息。

### 原始訊息傳送

- `.Raw_ob12(message: List[Dict])`：傳送 OneBot12 標準格式訊息
  - 支援複雜組合訊息（文字 + @用戶 + 回覆 + 媒體）
  - 自動將文字作為媒體訊息的 caption
- `.Raw_json(json_str: str)`：傳送原始 JSON 格式訊息

### 鏈式修飾方法

- `.At(user_id: str)`：@指定用戶（可多次呼叫）
- `.AtAll()`：@全體成員
- `.Reply(message_id: str)`：回覆指定訊息

### 方法名稱對應

傳送方法支援大小寫不敏感呼叫，透過對應表自動轉換為標準方法名：
```python
# 以下寫法等效
telegram.Send.To("group", 123).Text("hello")
telegram.Send.To("group", 123).text("hello")
telegram.Send.To("group", 123).TEXT("hello")
```

### 傳送範例

```python
# 基本文本傳送
await telegram.Send.To("group", group_id).Text("Hello World!")

# 媒體傳送（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="這是一張圖片")

# 媒體傳送（檔案上傳）
with open("image.jpg", "rb") as f:
    await telegram.Send.To("group", group_id).Image(f.read())

# @用戶
await telegram.Send.To("group", group_id).At("6117725680").Text("你好！")

# 回覆訊息
await telegram.Send.To("group", group_id).Reply("12345").Text("回覆內容")

# 組合使用
await telegram.Send.To("group", group_id).Reply("12345").At("6117725680").Image("https://example.com/image.jpg", caption="看這張圖")

# OneBot12 組合訊息
ob12_message = [
    {"type": "text", "data": {"text": "複雜組合訊息："}},
    {"type": "mention", "data": {"user_id": "6117725680", "name": "用戶名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)
```

### 不支援的方法提示

呼叫不支援的傳送方法時，會自動傳送文字提示：
```python
# 不支援的傳送類型
await telegram.Send.To("group", group_id).UnknownMethod("data")
# 將傳送：[不支援的傳送類型] 方法名: UnknownMethod, 參數: [...]
```

## 特有事件類型

Telegram 事件轉換到 OneBot12 協定，其中標準欄位完全遵守 OneBot12 協定，但存在以下差異：

### 核心差異點

1. 特有事件類型：
   - 內聯查詢：telegram_inline_query
   - 回調查詢：telegram_callback_query
   - 投票事件：telegram_poll
   - 投票答案：telegram_poll_answer

2. 擴展欄位：
   - 所有特有欄位均以 telegram_ 前綴識別
   - 保留原始資料在 telegram_raw 欄位
   - 頻道訊息使用 detail_type="channel"

### 事件監聽方式

Telegram 適配器支援兩種方式監聽事件：

```python
# 使用原始事件名
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass

# 使用對應後的事件名
@sdk.adapter.Telegram.on("message")
async def handle_message(event):
    pass
```

### 特殊欄位範例

```python
# 回調查詢事件
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_data": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# 內聯查詢事件
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_inline_query": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# 頻道訊息
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_chat": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

## 擴展欄位說明

- 所有特有欄位均以 `telegram_` 前綴識別
- 保留原始資料在 `telegram_raw` 欄位
- 頻道訊息使用 `detail_type="channel"`
- 訊息內容中的實體（如粗體、連結等）會轉換為對應的訊息段
- 回覆訊息會新增 `telegram_reply` 類型的訊息段

## 設定選項

Telegram 適配器支援以下設定選項：

### 基本設定
- `token`: Telegram Bot Token
- `proxy_enabled`: 是否啟用代理

### 代理設定
- `proxy.host`: 代理伺服器位址
- `proxy.port`: 代理埠號
- `proxy.type`: 代理類型 ("socks4" 或 "socks5")

### 執行模式

Telegram 適配器僅支援 **Polling（輪詢）** 模式，Webhook 模式已移除。

設定範例：
```toml
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
proxy_enabled = false

[Telegram_Adapter.proxy]
host = "127.0.0.1"
port = 1080
type = "socks5"