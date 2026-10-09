# 會話收件箱（Transcript）

會話收件箱會自動記錄機器人收發的訊息（依會話鍵 `platform:detail_type:target_id` 組織），
為對話恢復（`event.history`）、影子模組 diff、冷啟動回放等提供歷史資料。
本文檔說明它的**儲存模型、保留策略旋鈕各保護什麼**，以及執行時覆蓋 API 與放開限制的真實代價。

> 改限制前請先讀完「風險與審計」一節——每個旋鈕都有它存在的理由。

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

## 配置

```toml
[ErisPulse.transcript]
enabled = true          # 是否自動記錄
max_per_session = 50    # 單會話保留條數（0 = 關閉該會話裁剪）
ttl_hours = 168.0       # 全局保留時長（小時，0 = 永不清理）
```

環境變數覆蓋同樣生效：`ERISPULSE_TRANSCRIPT_MAX_PER_SESSION`、`ERISPULSE_TRANSCRIPT_TTL_HOURS`。  
配置變更熱生效（寫緩衝落盤節奏內，最多延遲 ~1 秒）。

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