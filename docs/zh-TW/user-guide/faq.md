# 常見問題（FAQ）

> [!TIP]
> **什麼時候需要讀這篇**：執行中出現「機器人沒反應 / 訊息遺失 / database is locked / 記憶體持續上漲」等現象時，先在這裡對照症狀找原因與排查路徑；沒命中再看對應的專題文檔。

## 訊息與事件

### 群裡 @ 機器人，機器人沒反應？

按順序核對：

1. **多帳戶部署 + `cross_account_policy = "drop"`**：被 @ 的帳戶副本有 at 點名優待（必定放行），但請確認目標帳戶的身分口徑——綁定表／歸屬判定用 `self.user_id` 與 `self.account_id` 雙口徑（見 [跨帳戶重複受理](../developer-guide/adapters/core-concepts.md)）
2. **`ignore_self`**：發送者 == 接收帳戶自身時事件被過濾（預設開啟），確認不是自己的回聲
3. **處理器條件**：`on()` 註冊的 `detail_type` / 文字條件是否符合事件實際欄位；事件缺少 `detail_type` 時，宣告了條件的處理器不再命中
4. **模組休眠／懶載入**：`activate_on` 未觸發的模組不會載入（見 [懶載入與休眠](../advanced/lazy-loading.md)）

### 同一條訊息機器人回覆了兩次？

- 多帳戶同群：兩帳戶各收到一份副本——開啟 `cross_account_policy`（內容級去重）或設定 `session_accounts`（會話精確歸屬，見 [配置](configuration.md)）
- 同優先級多處理器命中同一事件：各自獨立副本並行執行，處理器的 `mark_processed` 才會阻斷後續——核對你的處理器註冊條件

## 儲存與資料庫

### `database is locked` 反覆出現？

SQLite 的鎖互斥只發生在**寫與寫**之間（WAL 下讀寫不互斥）。高頻觸發時依序排查：

1. **長事務**：框架對持鎖超過 1s 的事務輸出告警並附開啟位置（`事務持鎖 x.xx s ...`）——按告警將慢操作移出事務區塊
2. **同步 API 阻塞**：`儲存同步 API 在非同步上下文呼叫` 告警指出的呼叫點遷移為 a 前綴非同步方法（`set` → `aset`）——handler 逾時同根因同處置，見本條第 1、2 步
3. **寫鎖排隊耐心**：調大 `ErisPulse.storage.sqlite.busy_timeout`（重啟後生效）
4. 仍無法解決 → 完整排查矩陣見 [儲存後端](../advanced/storage-backends.md)

### 升級後寫入報 `StorageOperationError`？

2.12.0 起寫入失敗**拋出例外而非靜默 `False`**——按 [升級遷移指南](migration.md) 改為 try/except。

## 執行環境

### 事件 handler 大量逾時 / 機器人間歇性沒反應？

典型根因：**handler 內呼叫了同步儲存 API**（每次呼叫阻塞事件迴圈直到完成）。特徵：`儲存同步 API 在非同步上下文呼叫` 的限頻告警 + handler 逾時集中爆發。處置：按告警呼叫點遷移 `aset` / `aget` / `aExecute`（見 [升級遷移指南](migration.md)）。

### 記憶體持續上漲怎麼辦？

1. 開啟 `ErisPulse.framework.memory_tracing = true`（排障時開啟，常態關閉）——`/metrics` 與記憶體快照會輸出 traced 記憶體與 top 配置點
2. 觀察 GC 週期日誌中的快照趨勢（`log_snapshot`）；框架的主動 GC 任務按記憶體增長自動全量回收
3. 熱重載重度使用後記憶體上漲：2.12.1 起卸載鏈路會解凍回收（舊版本的 `gc.freeze` 盲區已修）——升級框架
4. 模組自身容器無上限增長屬於模組責任——歸屬資源用 owner 上下文登記（見 [歸屬權系統](../advanced/ownership.md)）

### 熱重載後模組「消失了」？

熱重載卸載時會取消歸屬任務、回收歸屬資源；模組如果在 `on_unload` 之外自行建立任務/執行緒且未登記歸屬，框架無法兜底——統一用 `self.spawn()` / `spawn_background(owner=...)` 建立（見 [歸屬權系統](../advanced/ownership.md)）。

## 設定與部署

### 改了設定沒生效？

- **支援熱更新**的鍵（如 `cross_account_policy`、`event_dedupe`、`memory_tracing`、GC 參數）變更即時生效
- **需重啟**的鍵（`storage.use_global_db`、`storage.sqlite.busy_timeout`、router cors/security）變更時框架會輸出「需重啟程序後生效」告警——看到告警就重啟；`storage.backend` 變更同樣需重啟（目前無告警提示，改完記得重啟）
- 編輯中途語法錯誤：框架保留上次有效設定並輸出診斷（不會廣播空設定）

### 容器裡 `epsdk restart` 容器退出了？

容器內（PID 1）的 restart 已改為發送 `SIGUSR1` 觸發程序內軟重啟——需要此行為請升級到 2.12.0+；整個程序的重啟交給容器 restart 策略。

## 下一步

- 症狀未命中 → [儲存後端排查矩陣](../advanced/storage-backends.md) · [效能基準與調校](../advanced/performance.md)
- 懷疑框架缺陷 → [Bug 追蹤](../bug-tracker.md) · 提交 issue 前先跑 `ep doctor`
- 版本行為差異核對 → [升級遷移指南](migration.md)