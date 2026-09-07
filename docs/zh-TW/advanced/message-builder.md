# MessageBuilder 詳解

`MessageBuilder` 是 ErisPulse 提供的 OneBot12 標準訊息段建構工具，用於建構結構化的訊息內容，配合 `Send.Raw_ob12()` 使用。

## 導入方式

`MessageBuilder` 支援以下兩種導入方式（效果相同，推薦使用第一種）：

```python
from ErisPulse.Core.Event import MessageBuilder        # 推薦，透過套件匯出
from ErisPulse.Core.Event.message_builder import MessageBuilder  # 直接導入模組
```

## 雙模式機制

MessageBuilder 提供兩種使用模式，透過 Python 描述符機制（`__get__`）實現類別層級和實例層級的不同行為：當透過類別呼叫方法時，`__get__` 返回靜態方法的執行結果；當透過實例呼叫時，返回 `self` 以支援鏈式呼叫。

### 鏈式呼叫模式（實例）

透過實例化 `MessageBuilder()` 使用，每個方法返回 `self`，支援鏈式呼叫，最後用 `.build()` 取得訊息段列表：

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("你好！")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "你好！"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### 快速建立模式（靜態）

透過類別直接呼叫方法，每個方法直接返回訊息段列表，適合單段訊息：

```python
# 直接返回 list[dict]，無需 .build()
segments = MessageBuilder.text("你好！")
# [{"type": "text", "data": {"text": "你好！"}}]
```

## 消息段類型

| 方法 | 類型 | 數據參數 | 說明 |
|------|------|---------|------|
| `text(text)` | text | `text` | 文本消息 |
| `image(file)` | image | `file` | 圖片消息 |
| `audio(file)` | audio | `file` | 音頻消息 |
| `video(file)` | video | `file` | 視頻消息 |
| `file(file, filename?)` | file | `file`, `filename` | 文件消息 |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | @提及用戶 |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | `mention` 的別名 |
| `reply(message_id)` | reply | `message_id` | 回覆消息 |
| `at_all()` | mention_all | - | @全體成員 |
| `custom(type, data)` | 自定義 | 自定義 | 自定義消息段 |

## 配合 Send 使用

建構的消息段列表透過 `Send.Raw_ob12()` 發送：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# 鏈式建構 + 發送
segments = (
    MessageBuilder()
    .mention("user123", "張三")
    .text(" 請查看這張圖片")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### 配合 Event 回覆

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 日報彙總\n")
        .text("今日完成任務: 5\n")
        .text("進行中任務: 3")
        .build()
    )
```

## 工具方法

### copy()

複製當前的建構器，用於基於相同的基礎內容建立多個訊息變體：

```python
base = MessageBuilder().text("基礎內容").mention("admin")

# 基於相同的前綴建立不同的訊息
msg1 = base.copy().text(" 變體A").build()
msg2 = base.copy().text(" 變體B").image("img.jpg").build()
```

### clear()

清除已添加的訊息段，重用同一個建構器：

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" 你好！").build()
    await adapter.Send.To("user", user_id).Raw_ob12(msg)
```

### len() / bool()

```python
builder = MessageBuilder()
print(bool(builder))   # False

builder.text("Hello")
print(len(builder))    # 1
print(bool(builder))   # True
```

## 自訂消息段

使用 `custom()` 方法添加平台擴展消息段：

```python
# 添加平台特有的消息段
segments = (
    MessageBuilder()
    .text("請填寫表單：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> 自訂消息段只在對應平台的適配器中有效，其他適配器會忽略不認識的消息段。

## 完整範例

### 多元素訊息

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # 回覆原訊息
    .mention(event.get_user_id())             # @發送者
    .text(" 這是你的查詢結果：\n")             # 文字
    .image("https://example.com/chart.png")   # 圖片
    .text("\n詳細資料見附件：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### 靜態工廠 + 鏈式混合

```python
# 快速建構單段訊息
simple_msg = MessageBuilder.text("簡單文字")

# 鏈式建構複雜訊息
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 公告：")
    .text("今天下午3點開會")
    .build()
)
```

## 相關文件

- [適配器 SendDSL 詳解](../developer-guide/adapters/send-dsl.md) - Send 鏈式發送介面
- [事件轉換標準](../standards/event-conversion.md) - 消息段轉換規範
- [Event 包裝類](../developer-guide/modules/event-wrapper.md) - Event.reply_ob12() 方法