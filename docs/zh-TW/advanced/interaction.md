# 互動會話系統

> [!NOTE]
> 本章內容需要 ErisPulse **2.8.0+**。

ErisPulse 將「與使用者的持續互動」做成了框架級基礎設施：從一條 `wait_reply`，
到定時提醒、多路等待、會話互斥、重啟恢復，全部由統一的
**互動會話管理器**（`Core/Event/interaction.py`，`sdk.interaction`）調度。

{!--< tips >!--}
本文涵蓋的每一項能力都附帶**歸屬（owner）**：互動等待、租約、定時器全部記錄
註冊時的模組名，模組卸載 / 適配器關閉時由框架自動清理，等待方立即得到通知
而非干等超時——這是歸屬權系統在互動維度的延伸（見 [歸屬權系統](ownership.md)）。
{!--< /tips >!--}

## 等待回覆：wait_reply

`wait_reply` 是互動會話的基石——掛起當前協程，等待目標使用者在下一條訊息中「回覆」。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="請輸入你的名字:", timeout=30)
    if reply is None:
        await event.reply("超時了")
        return
    await event.reply(f"你好，{reply.get_text()}！")
```

### 全參數一覽

| 參數 | 說明 | 預設 |
|------|------|------|
| `prompt` | 掛起前發送的提示訊息 | None |
| `timeout` | 等待超時（秒） | 60 |
| `pattern` | glob 過濾（`*` / `?` / `[seq]`），不匹配繼續等待 | None |
| `regex` | 正則過濾（與 pattern 同時給定時須都匹配），不匹配繼續等待 | None |
| `validator` | 校驗函數（接收 Event，返回 bool），失敗繼續等待 | None |
| `callback` | 收到回覆時的回調（替代回傳值式的另一種寫法） | None |
| `method` | prompt 的發送方法 | "Text" |
| `session` | **會話級等待**：同會話（群 / 頻道）中任何人的回覆均可命中 | False |

```python
# 只接受數字金額，否則繼續等
reply = await event.wait_reply("請輸入金額:", regex=r"\d+\s*元", timeout=30)

# 會話級等待：群協作場景，任何群友回答均可
reply = await event.wait_reply(session=True, prompt="哪位大神幫忙答一下？")
```

### 等待會在什麼時候被取消

等待不再是「只能等超時」——以下情況會讓等待**立即終止**（`wait_reply` 返回 `None`），
而不是讓呼叫方一直等到超時：

| 觸發 | 取消原因（`InteractionCancelled.reason`） | 說明 |
|------|------|------|
| 歸屬模組被卸載 / 禁用 | `owner_unload` | 歸屬清理：誰註冊的等待，誰消失時一併回收 |
| 適配器關閉 / 重啟 | `platform_stop` | 該平台掛起的等待全部取消 |
| 同會話被新的等待 / 租約取代 | `conflict` | 見下方「會話仲裁」 |
| 回覆者被拉黑 / owner 模組被解綁 | `revoked` | 回覆命中的**權限複查**：scope 身份維度 + 模組維度 |
| 使用者回覆命中 | —— | 正常路徑，回傳回覆事件 |

底層異常為 `InteractionCancelled`（掛在 `InteractionError` 異常體系下），
`wait_reply` 已將其轉換為回傳 `None`；需要原因的呼叫方可直接使用
`sdk.interaction.register()` 低層 API。

### 回覆命中的完整判定鏈

一條回覆訊息到達時，互動管理器按以下順序判定（在命令匹配**之前**執行，
對話連續性優先——即使訊息已被其他高優先級處理器認領，掛起的對話也能完成）：

```
會話鍵命中（精確 user 維度 → 會話級回退）
  → pattern / regex 文本過濾（不匹配繼續等）
  → validator 校驗（失敗繼續等）
  → 權限複查（scope 身份維度 + owner 模組維度，失敗則終止等待）
  → 喚醒等待方 + 認領事件（mark_processed）
```

## 會話定時器：remind / escalate

將「超時」從回傳值轉為可編排的原語。定時器掛在互動會話上，  
隨模組卸載 / 適配器關閉自動取消，單會話活躍 remind 上限 5 個。

### remind：沒回覆就提醒

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("工單已提交，處理結果會在這裡通知")
    # 5 分鐘無回覆則溫和催一次；使用者任何回覆都會自動取消它
    event.remind(300, "還在嗎？有結果了會第一時間告訴你")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：到期向當前會話發送 `text`  
  （或執行 `callback(event)`，支援同步 / 異步）
- 回傳 `Reminder` 句柄：`reminder.cancel()` 手動取消、`reminder.expired` 查詢狀態
- 使用者在該會話**回覆後自動取消**——這正是「提醒」語意：  
  提醒只在使用者沉默時出現
- `Conversation` 內同樣可用：`conv.remind(120, "還在考慮嗎？")`

### escalate：到點必達的升級

```python
event.escalate(1800, lambda e: notify_master(f"工單 30 分鐘未處理：{event.get_command_args()}"))
```

與 `remind` 的唯一區別：**不受使用者回覆取消**——升級動作（通知主人、轉人工）  
是「超時必達」的承諾，僅手動 `cancel()` / 模組卸載 / 適配器關閉才取消。

| | `remind` | `escalate` |
|---|---|---|
| 到期行為 | 發文本 / 執行 callback | 執行 callback |
| 使用者回覆 | **自動取消** | 不受影響 |
| 歸屬清理（卸載 / 關平台） | 取消 | 取消 |
| 單會話上限 | 5 | 不限（隨歸屬清理兜底） |

## 多路等待：expect + select

同時掛起多條期望，**先到先得**——典型場景：等管理員審批的同時等用戶撤回、多人協作投票。

```python
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒絕*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "擱置", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒內未收到任何審批結果")
elif which == 0:
    await event.reply("已同意")
elif which == 1:
    await event.reply("已拒絕")
```

- `event.expect(...)` 建構**期望描述**（不註冊任何等待）：支援
  `pattern` / `regex` / `validator` / `user`（限定回覆者）/ `session`（任何人可答）
- `event.select(*expectations, timeout=60)`：統一註冊 → 任一命中即返回
  `(下標, 回覆事件)` → 未命中的等待自動取消；全部超時返回 `(None, None)`
- 命中的事件已被框架認領（`mark_processed`），不會被其他處理器重複消費

{!--< tips >!--}
`select` 與多線程 `asyncio.wait` 手工編排相比：期望未命中時自動清理、
命中事件自動認領、權限複查與歸屬清理全部生效——不需要自己管任何 Future。
{!--< /tips >!--}

## 會話互斥：acquire / hold / get_owner_of

歸屬權從「資源」走向「會話」——「這個使用者目前正被誰佔用」成為一等查詢。

```python
# 查詢：這個會話正被誰互動？（空閒返回 None）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 其他模組正在對話中，避免打擾

# 互斥租約：獨佔會話（deny 策略，被佔用返回 None）
lease = sdk.interaction.acquire(event)          # 默認 TTL 1 小時，可傳 ttl=
if lease is None:
    return  # 已被佔用
try:
    ...  # 獨佔互動
finally:
    lease.release()
```

上下文管理器形式（獲取失敗拋 `SessionOccupiedError`）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 退出自動釋放
```

租約支援 `renew(ttl)` 續期；TTL 慣性過期——過期的租約在下次存取時自動清理。

`Conversation.resume()` 恢復對話時框架會自動 acquire 租約（見
[Conversation 多輪對話](conversation.md)的「恢復即接管」）——
恢復的對話天然持有會話，其他模組不會插入。

## 會話收件箱：event.history

每會話近期訊息流的統一記錄（使用者 + 機器人雙方），作為 AI 上下文、
防重複回覆、行為分析類模組的**共享事實底座**——各模組不再各自儲存歷史。

```python
messages = await event.history(20)   # 當前會話最近 20 條，時間升序
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記錄：入站訊息（role=user）+ 機器人出站文字（role=bot）
- 儲存：獨立 SQLite 表，保留策略 = 每會話上限（預設 50）+ 全域 TTL（預設 7 天）
- 配置：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- 管理器 API：`sdk.transcript.append() / get() / clear()`

## 消息事務：message_tx

事務內的所有出站發送自動記帳；**異常退出時逆序自動撤回**已發送的訊息  
（適配器未實作 `delete_message` 時跳過，帳本仍正常記錄）。

```python
async with event.message_tx():
    await event.reply("正在處理，請稍候")
    result = await do_something()          # 這裡拋異常 →
    await event.reply(f"完成: {result}")   # 前面的"處理中"自動撤回
```

事務外發送不記帳（零開銷）；`get_send_receipts()` 可查看目前事務已發送的回執。

## 鏈路追蹤：trace-id

每個入站事件會自動獲得追蹤 ID（複用 `event["id"]`，若缺失則生成），貫穿：

- handler 上下文（`get_current_trace_id()` 讀取）
- 出站發送（`[Send]` 日誌行附加 `[trace:...]`，`message.sending/sent` 鈎子的 `trace_id` 欄位）
- 生命週期鈎子數據（dict 自動補 `_trace_id`）
- 定向事件（`emit_to`）與訊息事務回執

當一條訊息被多個模組接力處理時，全鏈路可使用同一 ID 串聯（日誌 / 慢查詢 / 審計）。

## 與其他系統的關係

- **歸屬權**：等待 / 租約 / 定時器全部記錄 owner，卸載即回收（[歸屬權系統](ownership.md)）
- **作用域**：回應命中複查身份 + 模組維度；跨模組呼叫審計走出站維度（[作用域](scope.md)）
- **Conversation**：多輪對話是交互會話之上的分支狀態機（[Conversation](conversation.md)），
  其等待同樣享有本頁全部取消 / 複查 / 歸屬語義

## 相關文件

- [Conversation 多輪對話](conversation.md) - 分支狀態機、自動檢查點與重新啟動恢復
- [歸屬權（owner）系統](ownership.md) - 歸屬清理的全景與設計邊界
- [作用域（scope）](scope.md) - 權限復查與出站審計的配置方式
- [模組間通訊](module-communication.md) - 跨模組呼叫與定向事件