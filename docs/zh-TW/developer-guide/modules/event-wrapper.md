# Event 包裝類別詳解

> [!NOTE]
> **L1 核心必讀**——首頁「閱讀路徑」中的五篇核心文件之一，模組開發必備。


處理器裡的 `event` 參數之所以能直接 `.get_text()` / `.reply()` / `.wait_reply()`，靠的就是 Event 包裝類別。本篇是它的完整方法清單——寫事件處理器時按需查閱，方法簽名與行為都以這裡為準。

## 為 event 參數添加類型註解

事件處理器的 `event` 參數是 **Event 包裝類**（dict 子類）。**強烈建議**為它添加 `Event` 類型註解（運行時無註解也能跑，註解服務於 IDE 自動完成與靜態檢查）：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE 自動補全所有便捷方法
    await event.reply(text)   # 拼寫錯誤在靜態檢查時即可發現
```

不加註解時 IDE 無法識別 Event 上的方法（`get_text()` / `reply()` / `wait_reply()` / 平台擴展方法均不提示），只能靠記憶拼寫。

> **注意區分**：事件處理器回調的 `event` 是 **Event 包裝類**（註解為 `Event`）；模組生命週期方法 `on_load` / `on_unload` 的 `event` 是普通 **dict**（註解為 `dict`），二者不要混淆。

## 核心特性

- **完全相容字典**：Event 繼承自 dict
- **便捷方法**：提供大量便捷方法
- **點式存取**：支援使用點號存取事件欄位
- **向後相容**：所有方法都是可選的

## 核心字段方法

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, 平台: {platform}, 時間: {time}")
```

## 消息事件方法

```python
from ErisPulse.Core.Event import message, Event

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")
```

## 消息類型判斷

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"類型: {'私聊' if is_private else '群聊'}")
```

## 回覆功能

```python
from ErisPulse.Core.Event import command, Event

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
    # 回覆必須匹配正則，否則繼續等待直到超時
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"收到金額：{reply.get_text()}")
```

#### reply 之外：send_chain

`reply()` 覆蓋不了的場景——平台專有修飾方法（如 Expire/Board 類）、連續多個修飾、
無內容參數的動作型發送——用 `event.send_chain` 獲取已設好目標與發送帳號的發送鏈，
自由追加修飾後發送：

```python
await event.send_chain.At(event.user_id).Text("內容")     # 鏈式修飾 + 發送
```

修飾方法清單見 [發送方法規範](../../standards/send-method-spec.md)。

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

## 命令資訊獲取

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"命令: {cmd_name}, 參數: {cmd_args}")
```

## 通知事件方法

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("歡迎添加我為好友！")
```

## 方法速查表

### 核心方法

#### 事件基礎資訊
- `get_id()` - 獲取事件ID
- `get_time()` - 獲取事件時間戳（Unix秒級）
- `get_type()` - 獲取事件類型（message/notice/request/meta）
- `get_detail_type()` - 獲取事件詳細類型（private/group/friend等）
- `get_platform()` - 獲取平台名稱

#### 机器人資訊
- `get_self_platform()` - 獲取機器人平台名稱
- `get_self_user_id()` - 獲取機器人用戶ID
- `get_self_account_id()` - 獲取機器人帳戶ID（多Bot模式）
- `get_self_info()` - 獲取機器人完整資訊字典

#### 會話標識
- `get_target_id()` - 獲取統一目標 ID（群聊返回 `group_id`，頻道返回 `channel_id`，私聊返回 `user_id`，按 group → channel → guild → thread → user 顺序取首个非空值）
- `get_session_id()` - 獲取會話唯一標識，格式為 `{platform}:{detail_type}:{target_id}`

### 消息事件方法

#### 消息內容
- `get_message()` - 獲取消息段數組（OneBot12格式）
- `get_alt_message()` - 獲取消息備用文本
- `get_text()` - 獲取純文本內容（`get_alt_message()` 的別名）
- `get_message_text()` - 獲取純文本內容（`get_alt_message()` 的別名）

#### 發送者資訊
- `get_user_id()` - 獲取發送者用戶ID
- `get_user_nickname()` - 獲取發送者暱稱
- `get_sender()` - 獲取發送者完整資訊字典

#### 群組/頻道資訊
- `get_group_id()` - 獵取群組ID（群聊消息）
- `get_channel_id()` - 獵取頻道ID（頻道消息）
- `get_guild_id()` - 獵取伺服器ID（伺服器消息）
- `get_thread_id()` - 獵取話題/子頻道ID（話題消息）

#### @消息相關
- `has_mention()` - 是否包含@機器人
- `get_mentions()` - 獵取所有被@的用戶ID列表

### 消息類型判斷

#### 基礎判斷
- `is_message()` - 是否為消息事件
- `is_private_message()` - 是否為私聊消息
- `is_group_message()` - 是否為群聊消息
- `is_at_message()` - 是否為@消息（`has_mention()` 的別名）

### 通知事件方法

#### 通知操作者
- `get_operator_id()` - 獵取操作者ID
- `get_operator_nickname()` - 獵取操作者暱稱

#### 通知類型判斷
- `is_notice()` - 是否為通知事件
- `is_group_member_increase()` - 群成員增加事件
- `is_group_member_decrease()` - 群成員減少事件
- `is_friend_add()` - 好友添加事件（匹配 `detail_type == "friend_increase"`）
- `is_friend_delete()` - 好友刪除事件（匹配 `detail_type == "friend_decrease"`）

### 請求事件方法

#### 請求資訊
- `get_comment()` - 獵取請求附言

#### 請求類型判斷
- `is_request()` - 是否為請求事件
- `is_friend_request()` - 是否為好友請求
- `is_group_request()` - 是否為群組請求

#### 請求審批（approve / reject）

註冊請求處理器並對請求做出決策：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # 請求標識（缺失時 approve/reject 抛 ValueError）
    if event.get_comment() == "暗號":
        result = await event.approve()    # 同意（可帶備註：approve(comment="歡迎")）
    else:
        result = await event.reject()     # 拒絕
    if result.get("status") != "ok":
        # 標準回應格式，失敗時 message 說明原因（如 34001 請求已過期）
        pass

@request.on_group_request()               # 群申請 / 群邀請
async def handle_group(event):
    await event.approve()
```

> 審批動作經適配器 `Request` DSL 執行；返回值、錯誤碼與適配器實現要求見
> [請求操作規範](../../standards/request-action-spec.md)。通用註冊器
> `request.on_request()`（不區分類型）同樣可用。

#### 鏈路控制（done / is_processed / is_stopped）

- `done(claim=True)` - 認領（預設）或僅阻斷後續低優先級處理器
- `is_processed()` - 當前事件是否已被認領
- `is_stopped()` - 當前事件處理鏈是否已被阻斷

認領與阻斷的完整語義（優先級交互、命令認領）見
[事件處理入門 · 鏈路控制：認領與阻斷](../../getting-started/event-handling.md#鏈路控制認領與阻斷)。

### 回覆功能

#### 基礎回覆
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 通用回覆方法
  - `content`: 發送內容（文本、URL等）
  - `method`: 發送方法，預設 "Text"，可選 "Image"/"Voice"/"Video"/"File" 等
  - `at_sender`: 是否@發送者（自動提取 user_id）
  - `quote`: 是否引用回覆當前消息（自動提取 message_id）
  - `at_users`: @用戶列表，如 `["user1", "user2"]`
  - `reply_to`: 手動指定回覆的消息 ID
  - `at_all`: 是否@全體成員
  - `**kwargs`: 額外參數（如 Mention 方法的 user_id）

- `reply_ob12(message)` - 使用 OneBot12 消息段回覆
  - `message`: OneBot12 消息段列表或字典，可配合 MessageBuilder 构建

#### 平台能力查詢
- `supports(method)` - 檢查當前平台是否支援某發送方法（如 `"Image"`、`"Voice"`），返回 `bool`
- `available_methods()` - 列出當前平台所有可用發送方法，返回方法名列表

#### 轉發功能

> **注意**：轉發功能需要通過適配器的 Send DSL 實現，Event 包裝類本身不提供直接的轉發方法。

```python
# 轉發消息到群組
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # 或指定其他群組ID
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **多帳戶部署**：處理事件的鏈路內發送**無需顯式指定帳戶**——框架在事件分發入口把觸發事件的帳戶標識注入調用上下文，`Send` / `Api` / `Request` 鏈路未顯式指定時自動綁定觸發事件的帳戶（顯式 `Using()` 永遠優先；定時器等無事件上下文場景走預設帳戶）。即上例轉發會從「收到這條事件的帳戶」發出，無需額外代碼。

#### 跨帳戶重複受理

多帳戶同群時，同一物理消息可能經多個帳戶各收到一遍。框架按 `ErisPulse.framework.cross_account_policy` 處理（預設 `off` 不關聯）：

- `mark`：後續副本照常分發，但事件頂層注入 `multi_receipt` 字段（`{"event_id": 首個受理事件id, "self_id": 首個受理帳戶}`）——模組讀取該字段自行裁決是否跳過回應
- `drop`：副本在分發入口直接丟棄，模組無感

### 等待回覆功能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - 等待用戶回覆
  - `prompt`: 提示消息，如果提供會發送給用戶
  - `timeout`: 等待超時時間（秒），預設60秒
  - `callback`: 回調函數，當收到回覆時執行
  - `validator`: 驗證函數，用於驗證回覆是否有效
  - `method`: 發送提示消息的方法，預設 "Text"
  - `pattern`: glob 通配符（`*` / `?` / `[seq]`），回覆文本必須匹配，不匹配則繼續等待
  - `regex`: 正則表達式，回覆文本必須匹配（`pattern` 與 `regex` 二選一），不匹配則繼續等待
  - 返回用戶回覆的 Event 對象，超時返回 None

#### 交互方法

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認對話
  - 返回 `True`（確認）/ `False`（否定）/ `None`（超時）
  - 內建中英文確認詞自動識別，可自定義詞集
  - `method`: 發送方法，預設 "Text"；支援 "Image"/"Markdown" 等非文本方式發送提示
  - `hint`: 是否在提示末尾自動追加確認詞提示（如 "（是/否）"），預設 False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選擇菜單
  - `options`: 選項文本列表
  - 返回選項索引（0-based），超時返回 `None`
  - `method`: 發送方法，預設 "Text"；文本類方法 (Text/Markdown/md/Html/h5) 預設合併選項到末尾
  - `options_format`: 選項格式（預設: "auto"，根據 method 自動選擇內建樣式）
    - `"auto"`：Markdown→無序列表（`- 1.選項`），Html→有序列表（`<ol>`），其他→純文本列表
    - `"list"`：每行一個，如 ``1. 選項A\n2. 選項B``
    - `"inline"`：單行展示，如 ``1.A | 2.B``
    - `"md"`：Markdown 無序列表
    - `"html"`：Html 有序列表
    - `callable`：自定義函數，接收 ``list[str]`` 返回 ``str``
  - `merge_prompt`: 是否強制合併為一條消息發送，預設 False
    - `False`（預設）：文本類方法自動合併；非文本方法先發 prompt 再發 Text 選項
    - `True`：無論什麼 method 都合併為一條消息，用用戶指定的 method 發送
  - `placeholder`: 選項插入佔位符，預設 `{options}`；prompt 中出現該標記的位置替換為選項文本，設為空字串則始終追加到末尾

- `collect(fields, timeout_per_field=60.0)` - 表單收集
  - `fields`: 字段列表，每項包含 `key`、`prompt`、可選 `validator`、可選 `method`
  - 返回 `{key: value}` 字典，任一字段超時返回 `None`
  - 每個 field 支持 `method` 鍵指定發送方法，例如收集圖片時用 `{"key": "avatar", "prompt": "請發送頭像", "method": "Image"}`
  - 每個 field 可選 `options` 鍵（列表），提供時該字段變為選擇題（自動調用 choose 逻辑）
  - 每個 field 可選 `options_format`、`merge_prompt`、`placeholder` 鍵，控制選項格式、消息合併行為和佔位符

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 等待任意事件
  - `condition`: 過濾函數，返回 `True` 時匹配
  - 返回匹配的 Event 對象，超時返回 `None`

- `conversation(timeout=60.0)` - 創建多輪對話上下文
  - 返回 `Conversation` 對象，支援 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - `is_active` 屬性表示對話是否活躍

#### 交互方法示例

**confirm() - 確認對話：**

```python
from ErisPulse.Core.Event import Event
@command("delete", help="刪除數據")
async def delete_handler(event: Event):
    if await event.confirm("確定要刪除所有數據嗎？"):
        sdk.storage.delete("all_data")
        await event.reply("數據已刪除")
    else:
        await event.reply("已取消")
```

**confirm() - 帶提示詞：**

```python
# hint=True 會在提示末尾追加 "（是/否）"
if await event.confirm("確定繼續？", hint=True):
    await event.reply("已繼續")
# 用戶看到：確定繼續？（是/否）
```

**choose() - 選擇菜單：**

```python
from ErisPulse.Core.Event import Event
@command("color", help="選擇顏色")
async def color_handler(event: Event):
    choice = await event.choose("請選擇顏色：", ["紅色", "綠色", "藍色"])
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
```

**choose() - 選項格式化與消息合併：**

```python
# inline 格式：選項顯示在同一行
choice = await event.choose("請選擇：", ["A", "B", "C"], options_format="inline")
# 輸出：1.A | 2.B | 3.C

# 自定義格式
choice = await event.choose("請選擇：", ["貓", "狗"],
    options_format=lambda opts: " / ".join(opts))
# 輸出：貓 / 狗

# options_format="auto"（預設）：根據 method 自動選擇內建樣式
# Markdown → 無序列表
choice = await event.choose(
    "## 請選擇", ["貓", "狗"],
    method="Markdown",  # auto 自動識別為 md 列表
)
# 輸出：
# ## 請選擇
# - 1. 貓
# - 2. 狗

# Html → 有序列表
choice = await event.choose(
    "<h2>請選擇</h2>", ["貓", "狗"],
    method="Html", merge_prompt=True,  # auto 自動識別為 html 列表
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

# 自定義佔位符
choice = await event.choose(
    "請選擇: [choices]",
    ["貓", "狗"],
    placeholder="[choices]",
)
```

**collect() - 表單收集：**

```python
from ErisPulse.Core.Event import Event
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
- `get_command_name()` - 獲取命令名稱
- `get_command_args()` - 獲取命令參數列表
- `get_command_raw()` - 獲取命令原始文本
- `get_command_info()` - 獲取完整命令資訊字典
- `is_command()` - 是否為命令

### 原始數據

- `get_raw()` - 獲取平台原始事件數據
- `get_raw_type()` - 獲取平台原始事件類型

### 平台擴展方法

適配器可以為 Event 包裝類註冊平台專有方法。方法僅在對應平台的 Event 實例上可用，其他平台訪問時拋出 `AttributeError`。

平台方法通過 `Event.__getattribute__` 优先於內建方法生效，因此可以覆寫 `confirm`、`choose`、`collect`、`wait_reply` 等內建交互方法，提供平台特色實現（如按鈕、卡片等）。內建實現作為 `_builtin_*` 函數導出供覆寫方調用。

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

### 跨平台擴展（通配符）

`register_event_method` 和 `register_event_mixin` 支援傳 `"*"` 作為平台名，註冊的方法在**所有平台**的 Event 實例上都可用。適合 AI 對話、上下文管理等需要跨平台複用的功能。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self 為 Event 實例，可訪問事件數據和內建方法
    await self.reply(f"AI: {prompt}")
```

註冊後，任何平台的事件處理器都能調用 `event.ai_chat(...)`。

方法解析優先級（從高到低）：平台特定方法 → 通配符方法 → 內建方法 → 字典鍵訪問。

> 適配器開發者註冊擴展方法的方式請參閱 [事件系統 API - 跨平台擴展通配符](../../api-reference/event-system.md#跨平台擴展通配符)。

## 相關文件

### 繼續模組開發路徑

- [模組開發入門](getting-started.md) - 建立第一個模組
- [模組最佳實踐](best-practices.md) - 開發高品質模組

### 深入互動能力

- [Conversation 多輪對話](../../advanced/conversation.md) - `wait_reply` 之上的完整會話引擎（收集、驗證、分支跳轉）