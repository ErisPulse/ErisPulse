# 會話收件箱（Transcript）

> [!TIP]
> **什麼時候需要閱讀本文**：需要消息歷史、對話恢復，或調整收件箱保留策略時。不需要則跳過，不會影響其他功能的使用。

會話收件箱會自動記錄機器人收發的消息（按會話鍵 `platform:detail_type:target_id` 組織），  
為對話恢復（`event.history`）、影子模組 diff、冷啟動回放等提供歷史數據。  
本文檔說明它的**儲存模型、保留策略旋鈕各保護什麼**，以及運行時覆蓋 API 與放開限制的真實代價。

> 改變限制前請先讀完「風險與審計」一節——每個旋鈕都有它存在的理由。

## 工作原理

```
訊息 ──append()──▶ 寫緩衝（記憶體 deque，硬上限 4096 行）
                        │  每 1 秒批量落盤（單批 ≤64 行，單事務）
                        ▼
              storage 後端的 transcript 表（預設 sqlite）
                        │  每 ~32 條追加惰性觸發一次保留清理
                        ▼
              ┌─ 按會話 FIFO 裁剪（max_per_session，預設 50 條）
              └─ 全局 TTL 刪除（ttl_hours，預設 168 = 7 天）
```

三個層級的保護，各自防的是不同的風險：

| 旋鈕 | 預設值 | 保護什麼 | 關閉（=0）的後果 |
|------|--------|----------|------------------|
| 寫緩衝上限 | 4096 行（常量，不可調） | **記憶體**：儲存不可用期間的積壓不撐爆 RAM | 不可關閉——這是記憶體防線 |
| 單條文字截斷 | 2000 字符（常量，不可調） | 單條訊息的記憶體/磁碟佔用 | 不可關閉 |
| `max_per_session` | 50 條/會話 | **磁碟增長**：單會話歷史無限堆積 | 該會話歷史無限增長 |
| `ttl_hours` | 168（7 天） | **磁碟增長**：全部會話的長期堆積 | `transcript` 表無限增長 |

關鍵認知：**寫緩衝有硬上限，所以放開保留策略不會直接撐爆記憶體**；
真正的風險在儲存層與下游消費者（見下節）。

> [!TIP]
> **不需要會話記憶的應用可以整體關閉**：`ErisPulse.transcript.enabled = false`
> 即停止入站/出站訊息的自動記錄——不寫記憶體緩衝也不寫儲存，省下常駐記憶體與持續的
> 儲存層 IO。會話收件箱主要服務 AI 上下文注入與防重複發送兩類需求，二者都不用的部署
> （如純命令型機器人）建議關閉。

## 配置

```toml
[ErisPulse.transcript]
enabled = true          # 是否自動記錄
max_per_session = 50    # 單會話保留條數（0 = 關閉該會話裁剪）
ttl_hours = 168.0       # 全局保留時長（小時，0 = 永不清理）
self_echo = "bot"       # 入站 bot 回聲處理：bot / skip / user
```

環境變量覆蓋同樣生效：`ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`、`ERISPULSE_TRANSCRIPT_TTL_HOURS`、
`ERISPULSE_TRANSCRIPT_SELF_ECHO`。配置變更熱生效（寫緩衝落盤節奏內，最多延遲 ~1 秒）。

> [!TIP]
> **不需要會話記憶就關閉它**：收件箱唯一的消費方是對話恢復 / 影子 diff / 冷啟動回放。
> 如果你的機器人（或部署的模塊）完全不用這些能力，設置 `enabled = false`
> 即可省下收件箱的記憶體緩衝與後台批量落盤 IO——訊息收發與命令處理完全不受影響。

## 消息歸因（sender 與 meta）

所有查詢介面（`get` / `recent` / `get_by_trace` / `event.history`）的每條記錄
統一攜帶歸因欄位，用於區分「誰說的 / 哪個模組發的」：

| 欄位 | 含義 |
|------|------|
| `sender` | 發送者標識：入站為 `user_id`，出站為 bot 賬號 / 回聲時的 `self.user_id` |
| `meta` | 記錄時刻的元數據（白名單契約，非完整 raw event） |

`meta` 白名單：

- **入站**：`nickname`（事件時刻的暱稱，事後反查拿到的是「現在的暱稱」）、
  `self_id`（bot 賬號）、`sub_type`、`message_id`；回聲訊息額外帶 `self_echo: true`；
- **出站**：發送上下文（`platform` / `method` / `detail_type` / `target_id` /
  `bot_id` / `trace_id` / `preview`）與 `module`（發送歸屬模組，見下）。

舊版本記錄（無 meta 列時期）的 `meta` 為 `{}`，呼叫方 `meta.get("nickname", "")`
自然降級；儲存後端不支援 ALTER 時同樣靜默回退 `{}`。

### 出站歸屬（meta.module）

同一實例上多個模組都會發訊息（聊天、管理、定時提醒）。出站記錄的 `meta.module`
標識發送歸屬，取值優先級為 `current_owner > current_caller > ""`：

| 發送場景 | module 值 |
|----------|-----------|
| 模組程式碼經 `module.call` 被呼叫期間 | 目標模組名 |
| 模組的事件處理器內發送 | 註冊該處理器的模組名（分發期自動注入） |
| 框架自身 / 無模組上下文 | `""` |

`message.sent` / `message.sending` 鈎子載荷（send_ctx）同樣攜帶 `module` 欄位。

### 入站 bot 回聲（self_echo）

部分平台/協議端會把 bot 自己發出的訊息以 message 事件回顯上報（如 OneBot v11 的
`report-self-message`、Telegram outgoing message）。框架在入站記錄前按
`self.user_id == user_id` 識別回聲，按 `self_echo` 配置處理：

| 取值 | 行為 |
|------|------|
| `"bot"`（預設） | 仍記錄，但 `role="bot"`、`sender=self_id`、`meta.self_echo=true` |
| `"skip"` | 不記錄（適配器同時會觸發 `message.sent` 時天然有出站記錄） |
| `"user"` | 記 `role="user"`（旧行為，相容逃生口） |

不回顯的平台（`self.user_id != user_id` 恆成立）行為與關閉本功能完全一致。

### 按會話過濾的 recent

```python
from ErisPulse import transcript

# 跨會話全域時間窗（冷啟動回放語義，預設）
transcript.recent(3600)

# 限定單會話：服務器端過濾，避免全域拉取後客戶端逐條比對 session_key
transcript.recent(3600, session_key="onebot11:group:123")
```

`session_key=None` 保持跨會話語義；空字串 `""` 等價不過濾（容錯）。

## 運行時覆蓋 API

需要在運行中動態調整（例如臨時為某個場景延長保留）時：

```python
from ErisPulse import transcript

# 覆蓋（優先於配置；僅駐記憶體，重啟後恢復配置值）
transcript.set_retention(max_per_session=500, ttl_hours=24 * 30)

# 查詢生效值與來源
transcript.get_retention()
# {'max_per_session': 500, 'ttl_hours': 720.0, 'overridden': ['max_per_session', 'ttl_hours']}

# 恢復按配置生效
transcript.reset_retention()
```

- 傳入 `0` = 關閉對應策略（會打 warning 日誌留痕）；負數拋 `ValueError`；
- 覆蓋在下次保留清理時生效（懶惰，最多延遲 ~32 條追加的節奏）；
- `transcript` 單例可從根包導入，也可 `sdk.transcript`。

## 風險與審計：解除限制前必讀

關閉 `max_per_session` / `ttl_hours`（或大幅調大）後，`transcript` 表會隨著訊息量 **無限增長**。後果鏈如下：

1. **磁碟空間耗盡**——sqlite 單一檔案持續膨脹，磁碟耗盡後框架儲存層將不可用；
2. **查詢效能退化**——`get()` / `recent()` / `get_by_trace()` 的掃描成本會隨著表增長而增加；
3. **下游記憶體壓力（OOM 的真正來源）**——將歷史整段載入記憶體的消費者（對話恢復帶歷史、面板全量拉取、你的業務程式碼 `get(session, n)` 取大量 n）會隨著表增長吃掉記憶體，在極端情況下會觸發 OOM kill。

**解除限制前請自問三件事**：要多久的歷史？要多大？誰來清理？  
如果答案依賴「永遠不刪除」，正確做法通常是外置歸檔（定期把舊資料搬到專用資料庫），而不是讓收件箱無限保留。

審計手段（定期檢查表規模）：

```python
# 經 ORM/SQL 建構器查行數與體積（以 sqlite 為例）
from ErisPulse import storage

row = storage.Table("transcript").raw_sql("SELECT COUNT(*) AS n FROM transcript")
```

```sql
-- 直接對 sqlite 檔案查詢（表體積）
SELECT COUNT(*) FROM transcript;
```

收到 `保留策略已被關閉` 的 warning 日誌 = 有人以 0 關閉了策略，請確認是自己的操作。

## 與其它機制的邊界

- **交互會話定時器 / wait_reply**：見 [交互會話系統](interaction.md)，與收件箱無關；
- **對話恢復的歷史帶回**：`resume(with_history=N)` 從收件箱取最近 N 條——
  收件箱被裁剪後能帶回的歷史隨之變少（調大 `max_per_session` 可延長可恢復窗口）；
- **影子模組 diff**：依賴 `get_by_trace` 鏈路查詢，TTL 過短的收件箱會縮短可 diff 窗口。

## 相關文件

- **消費收件箱歷史的地方**：對話恢復 [Conversation](conversation.md)、事件級讀取 [event.history](interaction.md#會話收件箱eventhistory)、影子 diff [影子模組與灰度轉正](shadow.md)
- **審計表規模用到的儲存介面** → [儲存後端](storage-backends.md) 與 [SQL 查詢建構器](sql-builder.md)