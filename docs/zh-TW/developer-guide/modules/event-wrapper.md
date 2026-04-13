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
target_id = event.get_group_id()  # 或指定其他群組ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 等待回覆功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None)` - 等待使用者回覆
  - `prompt`: 提示訊息，如果提供會發送給使用者
  - `timeout`: 等待超時時間（秒），預設 60 秒
  - `callback`: 回呼函數，當收到回覆時執行
  - `validator`: 驗證函數，用於驗證回覆是否有效
  - 返回使用者回覆的 Event 物件，超時返回 None

#### 互動方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None)` - 確認對話
  - 返回 `True`（確認）/ `False`（否定）/ `None`（超時）
  - 內建中英文確認詞自動識別，可自訂詞集

- `choose(prompt, options, timeout=60.0)` - 選擇選單
  - `options`: 選項文字列表
  - 返回選項索引（0-based），超時返回 `None`

- `collect(fields, timeout_per_field=60.0)` - 表單收集
  - `fields`: 欄位列表，每項包含 `key`、`prompt`、可選 `validator`
  - 返回 `{key: value}` 字典，任一欄位超時返回 `None`

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 過濾函數，返回 `True` 時匹配
  - 返回匹配的 Event 物件，超時返回 `None`

- `conversation(timeout=60.0)` - 建立多輪對話上下文
  - 返回 `Conversation` 物件，支援 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 屬性表示對話是否活躍

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

介面卡會為各自平台註冊專有方法，以下為常見範例（具體方法請參閱各 [平台文件](../../platform-guide/)）：

- `get_platform_event_methods(platform)` - 查詢指定平台已註冊的擴充方法列表
- 平台擴充方法僅在對應平台的 Event 實例上可用
- 可透過 `hasattr(event, "method_name")` 安全判斷方法是否存在

### 工具方法

- `to_dict()` - 轉換為普通字典
- `is_processed()` - 是否已被處理
- `mark_processed()` - 標記為已處理

### 點式存取

Event 繼承自 dict，支援點式存取所有字典鍵：

```python
platform = event.platform          # 等同於 event["platform"]
user_id = event.user_id          # 等同於 event["user_id"]
message = event.message          # 等同於 event["message"]
```

## 平台擴充方法

介面卡可以為 Event 包裝類註冊平台專屬方法。方法僅在對應平台的 Event 實例上可用，其他平台存取時拋出 `AttributeError`。

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