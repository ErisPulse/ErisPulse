# Event 包裝類別詳解

> [!NOTE]
> **L1 核心必讀**——首頁「閱讀路徑」中的五篇核心文件之一，模組開發必備。


處理器裡的 `event` 參數之所以能直接 `.get_text()` / `.reply()` / `.wait_reply()`，靠的就是 Event 包裝類別。本篇是它的完整方法清單——寫事件處理器時按需查閱，方法簽名與行為都以這裡為準。

## 為 event 參數添加類型註解

事件處理器的 `event` 參數是 **Event 包裝類別**（dict 子類別）。強烈建議為它添加類型註解：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE 自動補全所有便捷方法
    await event.reply(text)   # 拼寫錯誤在靜態檢查時即可發現
```

不加註解時 IDE 無法識別 Event 上的方法（`get_text()` / `reply()` / `wait_reply()` / 平台擴充方法均不提示），只能靠記憶拼寫。

> **注意區分**：事件處理器回呼的 `event` 是 **Event 包裝類別**（註解為 `Event`）；模組生命週期方法 `on_load` / `on_unload` 的 `event` 是普通 **dict**（註解為 `dict`），二者不要混淆。

## 核心特性

- **完全相容字典**：Event 繼承自 dict
- **便捷方法**：提供大量便捷方法
- **點式存取**：支援使用點號存取事件欄位
- **向後相容**：所有方法都是可選的

## 核心欄位方法

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, 平台: {platform}, 時間: {time}")
```

## 訊息事件方法

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")
```

## 訊息類型判斷

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"類型: {'私聊' if is_private else '群聊'}")
```

## 回覆功能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event: Event):
    await event.reply("請輸入你的名字:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")

@command("price")
async def price_command(event: Event):
    await event.reply("請輸入金額（如：5元）:")
    # 回覆必須匹配正規表示式，否則繼續等待直到逾時
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"收到金額：{reply.get_text()}")
```

## 互動會話進階

> [!NOTE]
> 本節能力需要 ErisPulse **2.8.0+**。

```python
# 會話定時提醒：5 分鐘無回覆則提醒，使用者回覆後自動取消
reminder = event.remind(300, "還在嗎？不想聊了回覆「退出」")
reminder.cancel()  # 也可手動取消

# 逾時升級：到點必達（不被回覆取消），如長時間未處理通知主人
event.escalate(1800, lambda e: notify_master("工單逾時"))

# 多路等待：同時等「同意」與「拒絕」，先到先得
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒絕*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("逾時未收到審批")

# 會話級等待：同群任何人的回覆均可命中（群協作）
reply = await event.wait_reply(session=True, prompt="哪位大佬幫忙答一下？")

# 會話收件匣：當前會話最近 20 條訊息（含機器人，AI 上下文 / 防複讀底座）
messages = await event.history(20)

# 訊息事務：例外時自動撤回事務內已傳送的訊息
async with event.message_tx():
    await event.reply("處理中，請稍候...")
    result = await do_something()
    await event.reply(f"完成：{result}")
```

## 命令資訊取得

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"命令: {cmd_name}, 參數: {cmd_args}")
```

## 通知事件方法

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("歡迎添加我為好友！")
```

## 方法速查表

### 核心方法

#### 事件基礎資訊
- `get_id()` - 取得事件ID
- `get_time()` - 取得事件時間戳記（Unix秒級）
- `get_type()` - 取得事件類型（message/notice/request/meta）
- `get_detail_type()` - 取得事件詳細類型（private/group/friend等）
- `get_platform()` - 取得平台名稱

#### 機器人資訊
- `get_self_platform()` - 取得機器人平台名稱
- `get_self_user_id()` - 取得機器人使用者ID
- `get_self_account_id()` - 取得機器人帳戶ID（多Bot模式）
- `get_self_info()` - 取得機器人完整資訊字典

#### 會話標識
- `get_target_id()` - 取得統一目標 ID（群聊返回 `group_id`，頻道返回 `channel_id`，私聊返回 `user_id`，按 group → channel → guild → thread → user 順序取首個非空值）
- `get_session_id()` - 取得會話唯一標識，格式為 `{platform}:{detail_type}:{target_id}`

### 訊息事件方法

#### 訊息內容
- `get_message()` - 取得訊息段陣列（OneBot12格式）
- `get_alt_message()` - 取得訊息備用文字
- `get_text()` - 取得純文字內容（`get_alt_message()` 的別名）
- `get_message_text()` - 取得純文字內容（`get_alt_message()` 的別名）

#### 傳送者資訊
- `get_user_id()` - 取得傳送者使用者ID
- `get_user_nickname()` - 取得傳送者暱稱
- `get_sender()` - 取得傳送者完整資訊字典

#### 群組/頻道資訊
- `get_group_id()` - 取得群組ID（群聊訊息）
- `get_channel_id()` - 取得頻道ID（頻道訊息）
- `get_guild_id()` - 取得伺服器ID（伺服器訊息）
- `get_thread_id()` - 取得話題/子頻道ID（話題訊息）

#### @訊息相關
- `has_mention()` - 是否包含@機器人
- `get_mentions()` - 取得所有被@的使用者ID清單

### 訊息類型判斷

#### 基礎判斷
- `is_message()` - 是否為訊息事件
- `is_private_message()` - 是否為私聊訊息
- `is_group_message()` - 是否為群聊訊息
- `is_at_message()` - 是否為@訊息（`has_mention()` 的別名）

### 通知事件方法

#### 通知操作者
- `get_operator_id()` - 取得操作者ID
- `get_operator_nickname()` - 取得操作者暱稱

#### 通知類型判斷
- `is_notice()` - 是否為通知事件
- `is_group_member_increase()` - 群成員增加事件
- `is_group_member_decrease()` - 群成員減少事件
- `is_friend_add()` - 好友添加事件（匹配 `detail_type == "friend_increase"`）
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
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 通用回覆方法
  - `content`: 傳送內容（文字、URL等）
  - `method`: 傳送方法，預設 "Text"，可選 "Image"/"Voice"/"Video"/"File" 等
  - `at_sender`: 是否@傳送者（自動提取 user_id）
  - `quote`: 是否引用回覆當前訊息（自動提取 message_id）
  - `at_users`: @使用者清單，如 `["user1", "user2"]`
  - `reply_to`: 手動指定回覆的訊息 ID
  - `at_all`: 是否@全體成員
  - `**kwargs`: 額外參數（如 Mention 方法的 user_id）

- `reply_ob12(message)` - 使用 OneBot12 訊息段回覆
  - `message`: OneBot12 訊息段清單或字典，可配合 MessageBuilder 建構

#### 平台能力查詢
- `supports(method)` - 檢查當前平台是否支援某傳送方法（如 `"Image"`、`"Voice"`），返回 `bool`
- `available_methods()` - 列出當前平台所有可用傳送方法，返回方法名清單

#### 轉發功能

> **注意**：轉發功能需要透過轉接器的 Send DSL 實作，Event 包裝類別本身不提供直接的轉發方法。

```python
# 轉發訊息到群組
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # 或指定其他群組ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 等待回覆功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - 等待使用者回覆
  - `prompt`: 提示訊息，如果提供會傳送給使用者
  - `timeout`: 等待逾時時間（秒），預設60秒
  - `callback`: 回呼函式，當收到回覆時執行
  - `validator`: 驗證函式，用於驗證回覆是否有效
  - `method`: 傳送提示訊息的方法，預設 "Text"
  - `pattern`: glob 萬用字元（`*` / `?` / `[seq]`），回覆文字必須匹配，不匹配則繼續等待
  - `regex`: 正規表示式，回覆文字必須匹配（`pattern` 與 `regex` 二選一），不匹配則繼續等待
  - 返回使用者回覆的 Event 物件，逾時返回 None

#### 互動方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認對話
  - 返回 `True`（確認）/ `False`（否定）/ `None`（逾時）
  - 內建中英文確認詞自動識別，可自訂詞集
  - `method`: 傳送方法，預設 "Text"；支援 "Image"/"Markdown" 等非文字方式傳送提示
  - `hint`: 是否在提示末尾自動附加確認詞提示（如 "（是/否）"），預設 False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選擇選單
  - `options`: 選項文字清單
  - 返回選項索引（0-based），逾時返回 `None`
  - `method`: 傳送方法，預設 "Text"；文字類方法 (Text/Markdown/md/Html/h5) 預設合併選項到末尾
  - `options_format`: 選項格式（預設: "auto"，根據 method 自動選擇內建樣式）
    - `"auto"`：Markdown→無序清單（`- 1.選項`），Html→有序清單（`<ol>`），其他→純文字清單
    - `"list"`：每行一個，如 ``1. 選項A\n2. 選項B``
    - `"inline"`：單行展示，如 ``1.A | 2.B``
    - `"md"`：Markdown 無序清單
    - `"html"`：Html 有序清單
    - `callable`：自訂函式，接收 ``list[str]`` 返回 ``str``
  - `merge_prompt`: 是否強制合併為一條訊息傳送，預設 False
    - `False`（預設）：文字類方法自動合併；非文字方法先發 prompt 再發 Text 選項
    - `True`：無論什麼 method 都合併為一條訊息，用使用者指定的 method 傳送
  - `placeholder`: 選項插入佔位符，預設 `{options}`；prompt 中出現該標記的位置替換為選項文字，設為空字串則始終附加到末尾

- `collect(fields, timeout_per_field=60.0)` - 表單收集
  - `fields`: 欄位清單，每項包含 `key`、`prompt`、可選 `validator`、可選 `method`
  - 返回 `{key: value}` 字典，任一欄位逾時返回 `None`
  - 每個 field 支援 `method` 鍵指定傳送方法，例如收集圖片時用 `{"key": "avatar", "prompt": "請發送頭像", "method": "Image"}`
  - 每個 field 可選 `options` 鍵（清單），提供時該欄位變為選擇題（自動呼叫 choose 邏輯）
  - 每個 field 可選 `options_format`、`merge_prompt`、`placeholder` 鍵，控制選項格式、訊息合併行為和佔位符

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 過濾函式，返回 `True` 時匹配
  - 返回匹配的 Event 物件，逾時返回 `None`

- `conversation(timeout=60.0)` - 建立多輪對話上下文
  - 返回 `Conversation` 物件，支援 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 屬性表示對話是否活躍

#### 互動方法範例

**confirm() - 確認對話：**

```python
@command("delete", help="刪除資料")
async def delete_handler(event: Event):
    if await event.confirm("確定要刪除所有資料嗎？"):
        sdk.storage.delete("all_data")
        await event.reply("資料已刪除")
    else:
        await event.reply("已取消")
```

**confirm() - 帶提示詞：**

```python
# hint=True 會在提示末尾附加 "（是/否）"
if await event.confirm("確定繼續？", hint=True):
    await event.reply("已繼續")
# 使用者看到：確定繼續？（是/否）
```

**choose() - 選擇選單：**

```python
@command("color", help="選擇顏色")
async def color_handler(event: Event):
    choice = await event.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
```

**choose() - 選項格式化與訊息合併：**

```python
# inline 格式：選項顯示在同一行
choice = await event.choose("請選擇：", ["A", "B", "C"], options_format="inline")
# 輸出：1.A | 2.B | 3.C

# 自訂格式
choice = await event.choose("請選擇：", ["貓", "狗"],
    options_format=lambda opts: " / ".join(opts))
# 輸出：貓 / 狗

# options_format="auto"（預設）：根據 method 自動選擇內建樣式
# Markdown → 無序清單
choice = await event.choose(
    "## 請選擇", ["貓", "狗"],
    method="Markdown",  # auto 自動識別為 md 清單
)
# 輸出：
# ## 請選擇
# - 1. 貓
# - 2. 狗

# Html → 有序清單
choice = await event.choose(
    "<h2>請選擇</h2>", ["貓", "狗"],
    method="Html", merge_prompt=True,  # auto 自動識別為 html 清單
)
# 輸出：
# <h2>請選擇</h2>
# <ol><li>1. 貓</li><li>2. 狗</li></ol>

# 合併模式 + 佔位符
choice = await event.choose(
    "## 請選擇\n{options}\n請回覆編號",
    ["貓", "狗"],
    method="Markdown", merge_prompt=True,
)

# 自訂佔位符
choice = await event.choose(
    "請選擇: [choices]",
    ["貓", "狗"],
    placeholder="[choices]",
)
```

**collect() - 表單收集：**

```python
@command("register", help="註冊")
async def register_handler(event: Event):
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

### 命令資訊

#### 命令基礎
- `get_command_name()` - 取得命令名稱
- `get_command_args()` - 取得命令參數清單
- `get_command_raw()` - 取得命令原始文字
- `get_command_info()` - 取得完整命令資訊字典
- `is_command()` - 是否為命令

### 原始資料

- `get_raw()` - 取得平台原始事件資料
- `get_raw_type()` - 取得平台原始事件類型

### 平台擴充方法

轉接器可以為 Event 包裝類別註冊平台專有方法。方法僅在對應平台的 Event 實例上可用，其他平台存取時拋出 `AttributeError`。

平台方法透過 `Event.__getattribute__` 優先於內建方法生效，因此可以覆寫 `confirm`、`choose`、`collect`、`wait_reply` 等內建互動方法，提供平台特色實作（如按鈕、卡片等）。內建實作作為 `_builtin_*` 函式匯出供覆寫方呼叫。

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

### 跨平台擴充（萬用字元）

`register_event_method` 和 `register_event_mixin` 支援傳 `"*"` 作為平台名，註冊的方法在**所有平台**的 Event 實例上都可用。適合 AI 對話、上下文管理等需要跨平台複用的功能。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self 為 Event 實例，可存取事件資料和內建方法
    await self.reply(f"AI: {prompt}")
```

註冊後，任何平台的事件處理器都能呼叫 `event.ai_chat(...)`。

方法解析優先順序（從高到低）：平台特定方法 → 萬用字元方法 → 內建方法 → 字典鍵存取。

> 轉接器開發者註冊擴充方法的方式請參閱 [事件系統 API - 跨平台擴充](../../api-reference/event-system.md#跨平台擴充萬用字元)。

## 相關文件

### 繼續模組開發路徑

- [模組開發入門](getting-started.md) - 建立第一個模組
- [模組最佳實踐](best-practices.md) - 開發高品質模組

### 深入互動能力

- [Conversation 多輪對話](../../advanced/conversation.md) - `wait_reply` 之上的完整會話引擎（收集、驗證、分支跳轉）