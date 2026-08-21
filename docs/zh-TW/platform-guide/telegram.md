# Telegram 平台特性文件

TelegramAdapter 是基於 Telegram Bot API 建立的適配器，支援多種訊息類型和事件處理。

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 文件資訊

- 對應模組版本: 4.1.1
- 維護者: ErisPulse

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 基本資訊

- 平台簡介：Telegram 是一個跨平台的即時通訊軟體
- 適配器名稱：TelegramAdapter
- 支援的協定/API版本：Telegram Bot API
- 會話類型映射：`private` → 發送時用 `user`，`group`/`supergroup` → `group`，`channel` → `channel`

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 支援的消息傳送類型

所有傳送方法均透過鏈式語法實作，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本傳送方法

| 方法 | 說明 | 參數 |
|------|------|------|
| `.Text(text)` | 發送純文字訊息 | `text: str` |
| `.Face(emoji)` | 發送表情骰子 | `emoji: str`（如 🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | 發送 Markdown 格式訊息 | `content_type` 預設為 `"MarkdownV2"` |
| `.HTML(text)` | 發送 HTML 格式訊息 | `text: str` |
| `.Sticker(file)` | 發送貼紙 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | 發送位置 | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | 發送地點 | 含標題和地址 |
| `.Contact(phone, first, last)` | 發送聯絡人 | 含電話號碼和姓名 |

### 媒體傳送方法

所有媒體方法支援 `bytes`（上傳）和 `str`（file_id / URL）兩種輸入：

| 方法 | 說明 |
|------|------|
| `.Image(file, caption, content_type)` | 發送圖片 |
| `.Video(file, caption, content_type)` | 發送影片 |
| `.Voice(file, caption)` | 發送語音 |
| `.Audio(file, caption, content_type)` | 發送音訊 |
| `.File(file, caption)` | 發送檔案 |
| `.Document(file, caption, content_type)` | `File` 的別名 |

### 訊息管理方法

| 方法 | 說明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 編輯已有訊息 |
| `.Recall(message_id)` | 刪除指定訊息 |
| `.Forward(from_chat_id, message_id)` | 轉發訊息（保留來源） |
| `.CopyMessage(from_chat_id, message_id)` | 複製訊息（不帶來源） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | 回應回調查詢 |

### 原始訊息傳送

- `.Raw_ob12(message: List[Dict])`：發送 OneBot12 標準格式訊息
- `.Raw_json(json_str: str)`：發送原始 JSON 格式訊息

### 鏈式修飾方法

| 方法 | 說明 |
|------|------|
| `.At(user_id)` | @指定用戶（透過 Telegram entities 實現，可多次呼叫） |
| `.AtAll()` | @全體成員（發送 `@All` 文字） |
| `.Reply(message_id)` | 回覆指定訊息 |
| `.Keyboard(inline_keyboard)` | 設定內聯鍵盤（`list[list[dict]]`） |
| `.ProtectContent(protect)` | 保護內容（防止轉發和保存） |
| `.Silent(silent)` | 靜默傳送（不通知使用者） |

### 傳送範例

```python
# 基本文本傳送
await telegram.Send.To("user", user_id).Text("Hello World!")

# 帶內聯鍵盤的訊息
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "按鈕1", "callback_data": "btn1"}, {"text": "按鈕2", "callback_data": "btn2"}],
    [{"text": "訪問官網", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("請選擇：")

# 媒體傳送（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="圖片")

# @用戶
await telegram.Send.To("group", group_id).At("6117725680").Text("你好！")

# 回覆 + 保護內容
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密訊息")

# 靜默傳送
await telegram.Send.To("group", group_id).Silent().Text("靜默通知")

# 回應回調查詢
await telegram.Send.AnswerCallback(callback_query_id, text="已處理", show_alert=False)

# OneBot12 組合訊息
ob12_message = [
    {"type": "text", "data": {"text": "複雜訊息："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "使用者名稱"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# 發送貼紙
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# 發送位置
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)

## 特有事件類型

Telegram 事件轉換遵循 OneBot12 標準，同時透過 `telegram_` 前綴提供平台擴展。

### 消息事件 detail_type 映射

| Telegram chat.type | OneBot12 detail_type | 發送目標類型 |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 特有事件類型

| detail_type | 說明 |
|---|---|
| `telegram_callback_query` | 回調查詢（內聯鍵盤按鈕點擊） |
| `telegram_inline_query` | 內聯查詢 |
| `telegram_chosen_inline_result` | 選擇的內聯結果 |
| `telegram_poll` | 投票事件 |
| `telegram_poll_answer` | 投票答案 |
| `telegram_my_chat_member` | Bot 自身成員狀態變更 |
| `telegram_chat_member` | 聊天成員變更 |
| `telegram_chat_join_request` | 加入聊天請求 |
| `telegram_shipping_query` | 運費查詢 |
| `telegram_pre_checkout_query` | 預付款查詢 |

### 標準消息段類型

轉換後的消息段使用 OneBot12 標準格式：

| 消息段類型 | 說明 | data 字段 |
|---|---|---|
| `text` | 純文字（不含 @用戶名） | `text` |
| `mention` | @用戶（標準 OB12） | `user_id`, `user_name` |
| `reply` | 回覆引用 | `message_id`, `user_id` |
| `image` | 圖片 | `file_id`, `url` |
| `video` | 影片 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | 語音 | `file_id`, `url`, `duration` |
| `audio` | 音頻 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | 檔案 | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置 | `latitude`, `longitude`, 可選 `title`, `address` |

### 平台擴展消息段

以 `telegram_` 前綴標識的擴展消息段：

| 消息段類型 | 說明 | data 字段 |
|---|---|---|
| `telegram_sticker` | 貼紙 | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF 動畫 | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 聯絡人 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | 內聯鍵盤 | `inline_keyboard` |

### 事件示例

#### 群聊消息（含 @提及）
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### 回調查詢事件
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### 內聯查詢事件
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### 帶內聯鍵盤的訊息
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "請選擇："}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "按鈕1", "callback_data": "btn1"}],
          [{"text": "訪問", "url": "https://example.com"}]
        ]
      }
    }
  ]
}

## Event Mixin 扩展方法

適配器註冊了以下平台專有方法，僅在 `platform == "telegram"` 時可用：

### 消息相關

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `is_bot_message()` | `bool` | 判斷消息是否來自機器人 |
| `is_edited_message()` | `bool` | 判斷是否為編輯過的消息 |
| `is_topic_message()` | `bool` | 判斷是否為主題/Topic 消息 |
| `get_update_id()` | `int` | 獲取 Telegram update ID |
| `get_chat_title()` | `str` | 獲取聊天標題 |
| `get_chat_username()` | `str` | 獲取聊天用戶名 |
| `get_forward_from()` | `dict` | 獲取轉發來源資訊 |
| `get_topic_id()` | `str` | 獲取主題 ID |

### 回調查詢相關

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_callback_data()` | `str` | 獲取回調查詢的 callback_data |
| `get_callback_id()` | `str` | 獲取回調查詢 ID（用於應答） |

### 消息段資料提取

| 方法 | 返回類型 | 說明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | 獲取消息中的內聯鍵盤 |
| `get_sticker_info()` | `dict` | 獲取貼紙資訊 |
| `get_contact_info()` | `dict` | 獲取聯絡人資訊 |
| `get_location()` | `dict` | 獲取位置資訊 |

### 使用範例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # 消息屬性
    if event.is_bot_message():
        return  # 忽略機器人消息

    if event.is_edited_message():
        print("這是編輯過的消息")

    # 聊天資訊
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 轉發來源
    forward = event.get_forward_from()

    # 消息段資料
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # 主題
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # 應答回調查詢
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="已點擊")

        # 回覆消息
        await event.reply(f"你點擊了：{callback_data}")

## 擴展欄位說明

- 所有獨有欄位均以 `telegram_` 前綴標識
- 保留原始資料在 `telegram_raw` 欄位
- 保留原始事件類型在 `telegram_raw_type` 欄位
- 頻道訊息使用 `detail_type="channel"`
- 私聊訊息使用 `detail_type="private"`（發送時需轉換為 `user`）
- 論題訊息包含 `thread_id` 欄位
- `@` 提及使用標準 `mention` 消息段類型（`type: "mention"`），文本中不含 @使用者名稱

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

## 配置選項

Telegram 适配器支援多帳號設定：

### 配置示例
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### 運行模式

Telegram 适配器僅支援 **Polling（輪詢）** 模式，Webhook 模式已移除。

### 代理配置

如需透過代理連線 Telegram API，請使用系統級代理（環境變數 `ALL_PROXY` / `HTTPS_PROXY`）。

### 舊版配置遷移

舊版單 token 配置會自動相容：
```toml
# 舊版格式（仍可使用，但建議遷移）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

建議遷移到新格式：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true