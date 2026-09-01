# 事件處理入門

本指南介紹如何處理 ErisPulse 中的各類事件。

## 事件類型概覽

ErisPulse 支援以下事件類型：

| 事件類型 | 說明 | 適用場景 |
|---------|------|---------|
| 消息事件 | 使用者發送的任何消息 | 聊天機器人、內容過濾 |
| 命令事件 | 以命令前綴開頭的消息 | 命令處理、功能入口 |
| 通知事件 | 系統通知（好友添加、群成員變化等） | 歡迎訊息、狀態通知 |
| 請求事件 | 使用者請求（好友請求、群邀請） | 自動處理請求 |
| 元事件 | 系統級事件（連接、心跳） | 連接監控、狀態檢查 |

## 消息事件處理

> **提示**: 建議在事件處理器中使用 `Event` 類型註解，以獲得 IDE 自動補全和類型檢查支援。

```python
from ErisPulse.Core.Event import Event  # 導入事件類型用於註解
```

### 監聽所有消息

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的訊息: {text}")
```

### 監聽私聊訊息

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！這是私聊訊息。")
```

### 監聽群聊訊息

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群 {group_id} 中 {user_id} 發送了訊息")
```

### 監聽@訊息

```python
@message.on_at_message()
async def at_handler(event: Event):
    # 獲取被@的使用者列表
    mentions = event.get_mentions()
    await event.reply(f"你@了這些使用者: {mentions}")
```

### 通配符與正則監聽

四個訊息裝飾器（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）均支援 `pattern`（glob 通配符）與 `regex`（正則），不匹配的訊息
**不會觸發**處理器：

```python
# glob 通配符：* 任意串、? 單字元、[seq] 字元集
@message.on_message(pattern="簽到*")
async def signin_handler(event: Event):
    await event.reply("簽到成功")

# 正則：匹配金額
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"收到金額：{event.get_text()}")

# pattern 與 regex 同時給出 → 兩者都須匹配
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` 同樣支援這兩個參數（見[等待回覆功能](../developer-guide/modules/event-wrapper.md#等待回覆功能)）。

## 命令事件處理

### 基本命令

```python
from ErisPulse.Core.Event import command

@command("help", help="顯示幫助訊息")
async def help_handler(event):
    help_text = """
可用命令：
/help - 顯示幫助
/ping - 測試連接
/info - 查看訊息
    """
    await event.reply(help_text)
```

### 命令別名

```python
@command(["help", "h"], aliases=["幫助"], help="顯示幫助訊息")
async def help_handler(event):
    await event.reply("幫助訊息...")
```

使用者可以使用以下任何方式呼叫：
- `/help`
- `/h`
- `/幫助`

### 命令參數

```python
@command("echo", help="回顯訊息")
async def echo_handler(event):
    # 獲取命令參數
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入要回顯的訊息")
    else:
        await event.reply(f"你說了: {' '.join(args)}")
```

### 命令組

```python
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    await event.reply("模組已重新載入")

@command("admin.stop", group="admin", help="停止機器人")
async def stop_handler(event):
    await event.reply("機器人已停止")
```

### 命令權限與存取控制

命令權限分三層，從上到下逐層判定（**上層拒絕則不再看下層**）：

```python
# ① 命令權限 ACL（使用者端設定）：按命令的使用者黑白名單，拒絕時回覆"權限不足"
# ② master=True —— 僅框架主人可執行（框架自動檢查，拒絕時回覆"權限不足"）
@command("restart", master=True, help="重啟模組")
async def restart_handler(event):
    await event.reply("模組已重啟")

# ③ permission=呼叫函數 —— 命令自身的控制邏輯（回傳 True 才執行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理介面")
async def panel_handler(event):
    await event.reply("歡迎來到管理介面")
```

**命令權限 ACL**（控制面 `ErisPulse.scope.commands`）：使用者可為任意命令設定使用者黑白名單，
命令名支援精確與 glob 模式（如 `"roll*"`），拒絕時回覆"權限不足"：

```toml
# config.toml —— 僅允許 123456 執行 restart；666 一律拒絕
[ErisPulse.scope.commands.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` 命中 → 拒絕；`allow` 非空且未命中 → 拒絕；否則交給開發者預設
（`master=True` / `permission`）。執行時 API（命令名支援 glob）：

```python
from ErisPulse import sdk
sdk.scope.allow_user("restart", "onebot11", "123456")   # 允許名單
sdk.scope.deny_user("restart", "onebot11", "666")       # 拒絕名單
sdk.scope.remove_acl("restart")                          # 清除黑白名單
sdk.scope.get_acl("restart")                             # 查詢當前名單
```

跨命令 / 跨使用者的**事件級**存取控制（某人 / 某群 / 某 Bot 的訊息收不收）
走控制面**身份維度**（`scope.identity`）；**模組級**可用性（哪些模組能用）
走控制面**模組維度**（`scope.platforms / bots / sessions`）。詳見[統一控制面](../advanced/scope.md)。

> 建議：命令內部需要聯動業務邏輯的用 `master=True` / `permission`；純按使用者 / 群做
> 存取控制的用控制面身份維度；控制模組可用性的用控制面模組維度。

### 命令優先級

```python
# 優先級數值越大，執行越早
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先級處理器")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先級處理器")
```

### 並行事件處理

ErisPulse 事件系統採用**同優先級並行、不同優先級串行**的調度模型：

```
事件到達
    ↓
priority=10 組: [處理器C ||處理器D] 並行 → 合併結果
    ↓ (如未中斷)
priority=0 組: [處理器A ||處理器B] 並行 → 合併結果
    ↓
...
```

- **同優先級並行**：優先級相同的多個處理器會同時執行，提高吞吐量
- **跨級串行**：不同優先級的組按順序執行（數值越大越先執行），確保高優先級處理器先運行
- **Copy-On-Write**：處理器無修改時不建立副本，確保零開銷
- **衝突處理**：同優先級多處理器修改同一欄位時，使用最後修改值並記錄警告日誌
- **中斷機制**：任意處理器呼叫 `event.done()`（預設）或 `event.done(claim=False)` 後，跳過後續低優先級組。認領與阻斷的區別見下文[「鏈路控制：認領與阻斷」](#鏈路控制認領與阻斷)

```python
# 示例：同優先級處理器並行執行
@message.on_message(priority=0)
async def handler_a(event):
    # 處理任務A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # 與 handler_a 並行執行
    event['result_b'] = process_b()

# 不同優先級串行執行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先級最高，最先執行
    pass
```

> **併發上限**：所有匹配 handler 的 Task 會**立即建立**，但透過一個信號量限制**同時在途執行數**，預設上限 **64**（`ErisPulse.framework.handler_max_concurrency`，支援熱更新）。超過上限的 Task 在信號量上排隊，等前面的完成後再進。事件洪峰時這就是你的「泄壓閥」。
>
> **慢日誌**：單個處理器耗時超過 **1 秒**時，框架會在日誌打 WARNING（`handler_slow`）。`wait_reply` 的等待時間會從耗時裡剔除，不會因為「等人回覆」誤報慢。

## 控制面過濾：為什麼我的模組沒收到訊息

事件到達後有兩道**靜默**過濾（都不回覆、不報錯）：

1. **身份維度**（`ErisPulse.scope.identity`）：事件進入分發入口時，按 使用者 > 群 > Bot > 適配器 判定收不收。
   被拒絕的**整個事件**直接丟棄，任何處理器（含命令分發器）都不會觸發。
2. **模組維度**（`ErisPulse.scope`）：事件到達某模組的處理器/命令時，按 會話 > Bot > 平台 判定
   該模組是否可用，**不通過就靜默跳過**。

```toml
# 例1：某群所有訊息不傳播
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：把 MyModule 屏蔽在某個 Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

此時該群的訊息到達時，`MyModule` 的命令與事件處理器**都不會被調度**。這不是 bug，是過濾機制——排查「模組沒反應」時優先檢查控制面的身份與模組綁定。

- 過濾日誌只在 **TRACE** 級可見（`core.scope.identity_denied` / `core.scope.denied`），預設 INFO 看不到任何痕跡
- 框架級處理器（如命令分發器 `scope_exempt=True`）不受**模組維度**影響，但受**身份維度**影響（整個事件已丟棄）
- 命令執行前還有第三道：命令權限 ACL（拒絕時回覆"權限不足"，見上節）

> 五維設定、匹配語法、執行時 API 見 [統一控制面](../../advanced/scope.md)。

## 鏈路控制：認領與阻斷

> [!NOTE]
> `event.done()` / `event.mark_processed()` 的 `claim=` / `stop=` 參數本特性需要 ErisPulse **2.7.1+**。

ErisPulse 將「認領」與「阻斷」兩個正交語意解耦，透過 `event.done()` 統一控制，便於在命令處理周圍疊加日誌、審計、權限等觀察層。

**兩個概念的準確定義：**

- **認領（claim）**：標記事件已被本處理器處理（寫入 `_processed`）。命令分發器看到已認領的事件會**跳過去重**——避免同一訊息被多個命令處理器重複處理。典型場景：命令匹配成功後認領，阻止命令分發器再介入。
- **阻斷（stop）**：阻止事件向**更低優先級**處理器傳播（寫入 `_propagation_stopped`）。低優先級處理器（如 `on_message`）將不再看到該事件。典型場景：高優先級處理器已完整處理事件，不希望低優先級再執行。

| `event.done(...)` | 認領 | 阻斷 | 場景 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | 命令 / 處理器處理完的標準做法 |
| `event.done(stop=False)` | ✔ | ✘ | 僅認領，讓低優先級觀察者（日誌 / 統計）繼續看到 |
| `event.done(claim=False)` | ✘ | ✔ | 僅阻斷（如防火牆 / 限流），但不做命令去重 |

`event.done(claim=, stop=)` 是 `event.mark_processed(claim=, stop=)` 的別名，二者參數與行為完全等價。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + 阻斷（命令處理完的標準做法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 僅認領：低優先級仍會執行（日誌 / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # 僅阻斷：低優先級不執行，但不做去重
```

### 命令與回覆的 block 設定

命令匹配成功 / `wait_reply` 匹配到回覆後，預設會阻斷傳播（向後相容）。可透過設定放行，讓低優先級處理器（日誌 / 審計 / 權限）也能觀測這些訊息：

```toml
[ErisPulse.event.command]
block = false   # 命令訊息繼續流向低優先級處理器

[ErisPulse.event.wait_reply]
block = false   # 被 wait_reply 消費的回覆繼續流向低優先級處理器
```

## 通知事件處理

### 好友添加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"歡迎添加我為好友，{nickname}！")
```

### 群成員增加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"歡迎新成員 {user_id} 加入群 {group_id}")
```

### 群成員減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成員 {user_id} 離開了群 {group_id}")
```

## 請求事件處理

### 好友請求

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友請求: {user_id}, 附言: {comment}")
    
    # 可以透過適配器 API 處理請求
    # 具體實作請參考各適配器文件
```

### 群邀請請求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀請，來自 {user_id}")
```

## 元事件處理

### 連接事件

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已連接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已斷開連接")
```

### 心跳事件

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳檢測")
```

### Bot 狀態查詢

當適配器發送 meta 事件後，框架自動追蹤 Bot 狀態，你隨時可以查詢：

```python
from ErisPulse import sdk

# 檢查某個 Bot 是否在線
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在線")

# 列出目前所有在線 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 獲取完整狀態摘要
summary = sdk.adapter.get_status_summary()
```

## 互動式處理

### 使用 reply 方法發送回覆

`event.reply()` 方法支援多種修飾參數，方便發送帶有 @、回覆等功能的訊息：

```python
# 簡單回覆
await event.reply("你好")

# 發送不同類型的訊息
await event.reply("http://example.com/image.jpg", method="Image")  # 圖片
await event.reply("http://example.com/voice.mp3", method="Voice")  # 聲音

# @單個使用者
await event.reply("你好", at_users=["user123"])

# @多個使用者
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 回覆訊息
await event.reply("回覆內容", reply_to="msg_id")

# @全體成員
await event.reply("公告", at_all=True)

# 組合使用：@使用者 + 回覆訊息
await event.reply("內容", at_users=["user1"], reply_to="msg_id")
```

### 等待使用者回覆

```python
@command("ask", help="詢問使用者")
async def ask_handler(event):
    await event.reply("請輸入你的名字:")
    
    # 等待使用者回覆，超時時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超時，請重新輸入。")
```

### 帶驗證的等待回覆

```python
@command("age", help="詢問年齡")
async def age_handler(event):
    def validate_age(event_data):
        """驗證年齡是否有效"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("請輸入你的年齡 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年齡是 {age} 歲")
    else:
        await event.reply("輸入無效或超時")
```

### 帶回調的等待回覆

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已確認！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("確認執行此操作嗎？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認對話 (confirm)

等待使用者確認或否定，自動識別內建中英文確認詞：

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    if await event.confirm("確定要執行此操作嗎？"):
        await event.reply("已確認，執行中...")
    else:
        await event.reply("已取消")

# 自訂確認詞
if await event.confirm("繼續嗎？", yes_words={"go", "繼續"}, no_words={"stop", "停止"}):
    pass
```

### 選擇選單 (choose)

使用者可回覆選項編號或選項文字：

```python
@command("choose", help="選擇")
async def choose_handler(event):
    choice = await event.choose(
        "請選擇顏色：",
        ["紅色", "綠色", "藍色"]
    )
    
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
    else:
        await event.reply("超時未選擇")
```

**合併模式**：`merge_prompt=True` 時將選項拼入提示訊息，用使用者指定的 `method` 一條訊息發送：

```python
# 用 Markdown 發送合併後的提示 + 選項
choice = await event.choose(
    "## 請選擇顏色\n{options}\n請回覆編號",
    ["紅色", "綠色", "藍色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` 占位符控制選項插入位置；不寫則追加到 prompt 末尾。
> 可透過 `placeholder` 參數自訂占位符（如 `placeholder="[choices]"`）。
> `options_format="auto"`（預設）根據 method 自動選擇樣式：Markdown→無序列表，Html→有序列表，其他→純文本列表。
> 文本類方法（Text/Markdown/Html 等）預設合併選項到末尾；非文本方法（Image 等）預設拆分為兩條訊息。

### 收集表單 (collect)

多步驟收集使用者輸入：

```python
@command("register", help="註冊")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "請輸入姓名："},
        {"key": "age", "prompt": "請輸入年齡：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "請輸入電子信箱："}
    ])
    
    if data:
        await event.reply(f"註冊成功！\n姓名：{data['name']}\n年齡：{data['age']}\n電子信箱：{data['email']}")
    else:
        await event.reply("註冊超時或輸入無效")
```

### 等待任意事件 (wait_for)

等待滿足條件的任意事件，不限於同一使用者：

```python
@command("wait_member", help="等待新成員")
async def wait_member_handler(event):
    await event.reply("等待群成員加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"歡迎新成員：{evt.get_user_id()}")
    else:
        await event.reply("等待超時")
```

### 多輪對話 (conversation)

建立可互動的多輪對話上下文：

```python
@command("survey", help="問卷調查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("歡迎參與問卷調查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("對話超時，再見！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再見！")
            break
        
        await conv.say(f"你說了：{text}，繼續輸入或回覆'退出'結束")
```

### 內建確認詞

ErisPulse 內建了中英文確認詞集合：

- **確認詞** (`CONFIRM_YES_WORDS`): 是、yes、y、確認、確定、好、好的、ok、true、對、嗯、行、同意、沒問題...
- **否定詞** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、錯、拒絕、不可以...

## 事件資料存取

### Event 物件常用方法

```python
@command("info")
async def info_handler(event):
    # 基礎資訊
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 發送者資訊
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 訊息內容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # 群組資訊
    group_id = event.get_group_id()
    
    # 機器人資訊
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始資料
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # 平台資訊
    platform = event.get_platform()
    
    # 訊息類型判斷
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # 命令資訊
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### 平台擴展方法

除了內建方法外，各平台適配器還會註冊平台專有方法，方便你存取平台特有的資料。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根據平台調用專有方法
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 專有方法
    elif platform == "email":
        subject = event.get_subject()           # 郵件專有方法
```

如果不確定平台是否註冊了某個方法，可以查詢某個平台註冊了哪些方法：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各平台註冊的專有方法請參閱對應的 [平台文件](../platform-guide/)。

## 事件處理最佳實踐

### 1. 錯誤處理

```python
@command("process")
async def process_handler(event):
    try:
        # 業務邏輯
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 預期的業務錯誤
        await event.reply(f"參數錯誤: {e}")
    except Exception as e:
        # 未預期的錯誤
        sdk.logger.error(f"處理失敗: {e}")
        await event.reply("處理失敗，請稍後重試")
```

### 2. 日誌記錄

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"處理訊息: {user_id} - {text}")
    
    # 使用模組自己的日誌
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細除錯資訊")
```

### 3. 條件處理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """條件處理 - 在處理器內部判斷"""
    # 只處理特定使用者的訊息
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 只處理包含特定關鍵字的訊息
    if "關鍵字" not in event.get_text():
        return
    
    await event.reply("條件滿足，處理訊息")
```

## 下一步

- [常見任務範例](common-tasks.md) - 學習常用功能的實現（含訊息發送進階：重試/超時/批量）
- [平台特性指南](../platform-guide/README.md) - Send DSL 鏈式發送、發送規則、批量建構的完整說明
- [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md) - 深入了解 Event 物件
- [使用者使用指南](../user-guide/) - 了解設定和模組管理