# Event 包裝類詳解

Event 模組提供了功能強大的 Event 包裝類，簡化事件處理。

## 核心特性

- **完全相容字典**：Event 繼承自 dict
- **便捷方法**：提供大量便捷方法
- **點式存取**：支援使用點號存取事件欄位
- **向後相容**：所有方法都是可選的

## 核心欄位方法

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, 平台: {platform}, 時間: {time}")
```

## 訊息事件方法

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")
```

## 訊息類型判斷

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"類型: {'私訊' if is_private else '群聊'}")
```

## 回覆功能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("請輸入你的名字:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
```

## 指令資訊獲取

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"指令: {cmd_name}, 參數: {cmd_args}")
```

## 通知事件方法

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("歡迎新增我為好友！")
```

## 方法速查表

### 核心方法

#### 事件基礎資訊
- `get_id()` - 取得事件 ID
- `get_time()` - 取得事件時間戳記（Unix 秒級）
- `get_type()` - 取得事件類型（message/notice/request/meta）
- `get_detail_type()` - 取得事件詳細類型（private/group/friend 等）
- `get_platform()` - 取得平台名稱

#### 機器人資訊
- `get_self_platform()` - 取得機器人平台名稱
- `get_self_user_id()` - 取得機器人使用者 ID
- `get_self_account_id()` - 取得機器人帳戶 ID（多 Bot 模式）
- `get_self_info()` - 取得機器人完整資訊字典

### 訊息事件方法

#### 訊息內容
- `get_message()` - 取得訊息段陣列（OneBot12 格式）
- `get_alt_message()` - 取得訊息備用文字
- `get_text()` - 取得純文字內容（`get_alt_message()` 的別名）
- `get_message_text()` - 取得純文字內容（`get_alt_message()` 的別名）

#### 發送者資訊
- `get_user_id()` - 取得發送者使用者 ID
- `get_user_nickname()` - 取得發送者暱稱
- `get_sender()` - 取得發送者完整資訊字典

#### 群組/頻道資訊
- `get_group_id()` - 取得群組 ID（群聊訊息）
- `get_channel_id()` - 取得頻道 ID（頻道訊息）
- `get_guild_id()` - 取得伺服器 ID（伺服器訊息）
- `get_thread_id()` - 取得話題/子頻道 ID（話題訊息）

#### @ 訊息相關
- `has_mention()` - 是否包含 @ 機器人
- `get_mentions()` - 取得所有被 @ 的使用者 ID 列表

### 訊息類型判斷

#### 基礎判斷
- `is_message()` - 是否為訊息事件
- `is_private_message()` - 是否為私訊
- `is_group_message()` - 是否為群聊訊息
- `is_at_message()` - 是否為 @ 訊息（`has_mention()` 的別名）

### 通知事件方法

#### 通知操作者
- `get_operator_id()` - 取得操作者 ID
- `get_operator_nickname()` - 取得操作者暱稱

#### 通知類型判斷
- `is_notice()` - 是否為通知事件
- `is_group_member_increase()` - 群成員增加事件
- `is_group_member_decrease()` - 群成員減少事件
- `is_friend_add()` - 好友新增事件（匹配 `detail_type == "friend_increase"`）
- `is_friend_delete()` - 好友刪除事件（匹配 `detail_type == "friend_decrease"`）

### 請求事件方法

#### 請求資訊
- `get_comment()` - 取得請求附言

#### 請求類型判斷
- `is_request()` - 是否為請求事件
- `is_friend_request()` - 是否為好友請求
- `is_group_request()` - 是否為群組請求

### 回覆功能

#### 基礎回覆
- `reply(content, method="Text", at_users=None, reply_to=None, at_all=False, **kwargs)` - 通用回覆方法
  - `content`: 傳送內容（文字、URL 等）
  - `method`: 傳送方法，預設 "Text"
  - `at_users`: @ 使用者列表，如 `["user1", "user2"]`
  - `reply_to`: 回覆訊息 ID
  - `at_all`: 是否 @ 全體成員
  - 支援 "Text", "Image", "Voice", "Video", "File", "Mention" 等
  - `**kwargs`: 額外參數（如 Mention 方法的 user_id）

- `reply_ob12(message)` - 使用 OneBot12 訊息段回覆
  - `message`: OneBot12 訊息段列表或字典，可配合 MessageBuilder 構建

#### 轉發功能

> **注意**：轉發功能需要透過介面卡的 Send DSL 實現，Event 包裝類本身不提供直接的轉發方法。

```python
# 轉發訊息到群組
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # 或指定其他群組 ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 等待回覆功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - 等待使用者回覆
  - `prompt`: 提示訊息，如果提供會發送給使用者
  - `timeout`: 等待超時時間（秒），預設 60 秒
  - `callback`: 回呼函數，當收到回覆時執行
  - `validator`: 驗證函數，用於驗證回覆是否有效
  - `method`: 發送提示訊息的方法，預設 "Text"
  - 返回使用者回覆的 Event 物件，超時返回 None

#### 互動方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text")` - 確認對話
  - 返回 `True`（確認）/ `False`（否定）/ `None`（超時）
  - 內建中英文確認詞自動識別，可自訂詞集
  - `method`: 發送方法，預設 "Text"；支援 "Image"/"Markdown" 等非文字方式發送提示

- `choose(prompt, options, timeout=60.0, method="Text")` - 選擇選單
  - `options`: 選項文字列表
  - 返回選項索引（0-based），超時返回 `None`
  - `method`: 發送方法；文字類方法 (Text/Markdown/Html) 將選項拼接到 prompt 一條訊息發送；富媒體方法先發富媒體內容再發 Text 選項列表

- `collect(fields, timeout_per_field=60.0)` - 表單收集
  - `fields`: 欄位列表，每項包含 `key`、`prompt`、可選 `validator`、可選 `method`
  - 返回 `{key: value}` 字典，任一欄位超時返回 `None`
  - 每個 field 支援 `method` 鍵指定發送方法，例如收集圖片時用 `{"key": "avatar", "prompt": "請發送頭像", "method": "Image"}`

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 過濾函數，返回 `True` 時匹配
  - 返回匹配的 Event 物件，超時返回 `None`

- `conversation(timeout=60.0)` - 建立多輪對話上下文
  - 返回 `Conversation` 物件，支援 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 屬性表示對話是否活躍

#### 互動方法示例

**confirm() - 確認對話：**

```python
@command("delete", help="刪除資料")
async def delete_handler(event):
    if await event.confirm("確定要刪除所有資料嗎？"):
        sdk.storage.delete("all_data")
        await event.reply("資料已刪除")
    else:
        await event.reply("已取消")
```

**choose() - 選擇選單：**

```python
@command("color", help="選擇顏色")
async def color_handler(event):
    choice = await event.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
```

**collect() - 表單收集：**

```python
@command("register", help="註冊")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "請輸入姓名："},
        {"key": "age", "prompt": "請輸入年齡：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"註冊成功！{data['name']}，{data['age']}歲")
```

**非 Text 方法的 reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("看這張圖：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完整的 Conversation 多輪對話用法請參考 [Conversation 多輪對話](../../advanced/conversation.md)。

### 指令資訊

#### 指令基礎
- `get_command_name()` - 取得指令名稱
- `get_command_args()` - 取得指令參數列表
- `get_command_raw()` - 取得指令原始文字
- `get_command_info()` - 取得完整指令資訊字典
- `is_command()` - 是否為指令

### 原始資料

- `get_raw()` - 取得平台原始事件資料
- `get_raw_type()` - 取得平台原始事件類型

### 平台擴充方法

介面卡可以為 Event 包裝類註冊平台專屬方法。方法僅在對應平台的 Event 實例上可用，其他平台存取時拋出 `AttributeError`。

平台方法透過 `Event.__getattribute__` 优先於內建方法生效，因此可以覆寫 `confirm`、`choose`、`collect`、`wait_reply` 等內建互動方法，提供平台特色實現（如按鈕、卡片等）。內建實現作為 `_builtin_*` 函數導出供覆寫方調用。

```python
# 郵件事件 - 只有郵件方法
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ 返回 "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram 事件 - 只有 Telegram 方法
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ 返回 "private"
event.get_subject()      # ❌ AttributeError

# 內建方法始終可用
event.get_text()         # ✅ 任何平台
event.reply("hi")        # ✅ 任何平台
```

### 查詢已註冊方法

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` 和 `dir` 支援

```python
hasattr(event, "get_subject")   # 僅當 platform="email" 時返回 True
"get_subject" in dir(event)     # 同上
```

> 介面卡開發者註冊擴充方法的方式請參閱 [事件系統 API - 介面卡：註冊平台擴充方法](../../api-reference/event-system.md#介面卡註冊平台擴充方法)。

## 相關文件

- [模組開發入門](getting-started.md) - 建立第一個模組
- [最佳實踐](best-practices.md) - 開發高品質模組