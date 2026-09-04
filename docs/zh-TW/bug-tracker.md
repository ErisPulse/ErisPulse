# Bug 追蹤器

本文檔記錄 ErisPulse SDK 的已知 Bug 及其修復情況，按修復版本時間順序排列。

> **寫給讀者**
> 沒有任何軟體天生完美，再細心的開發者也會留下小錯誤。本追蹤收錄的都是對運行有實際影響的問題——那些過於細微、連「輕微」等級都達不到的瑕疵並不會出現在這裡。清單中「嚴重」項看起來不少，但公開記錄這些 Bug 的初衷是讓排查與回溯更順暢，而非製造焦慮：能被看見、被記錄、被修復的問題，本身就是項目不斷變好的證明。看到這份清單不必緊張，它是一份排查工具，而不是恐懼的來源。

> **如何閱讀 & 維護約定**
> - 每條 Bug 記錄包含問題描述、根因分析、影響版本範圍、修復方案等結構化字段，建議升級前先檢索「影響版本」是否覆蓋當前使用的版本。
> - 如需新增 Bug 條目，請在對應位置補充內容，遵循下文字段規範與嚴重性/類型分類。

---

## 字段說明

### 必填字段

| 字段 | 說明 |
|------|------|
| **問題** | Bug 的外在表現、使用者可觀察到的異常現象。盡量給出具體錯誤訊息或典型場景 |
| **原因** | 根因分析，指向具體的程式碼缺陷（含「根因鏈路」圖示用於複雜場景） |
| **影響版本** | 受影響的版本區間，格式 `引入版本 - 修復版本`（含兩端 dev 版本） |
| **修復版本** | 修復該 Bug 的具體版本號 |
| **修復內容** | 修復方案的簡要描述，含關鍵程式碼變更點 |
| **修復日期** | 對應修復版本的發布日期，採用 `YYYY/MM/DD` 格式 |
| **嚴重性** | 按下文「嚴重性分級」標註 |
| **類型** | 按下文「類型分類」標註，可組合（如 `適配器 / 路由`） |

### 可選字段

| 字段 | 說明 | 適用場景 |
|------|------|---------|
| **重現步驟** | 觸發該 Bug 的最小可重現路徑 | 複雜 Bug、偶發性 Bug 建議補充 |
| **關聯** | 相關 Issue / PR / Commit 鏈接 | 有外部討論記錄時補充 |
| **回歸測試** | 驗證修復、防止再次回歸的測試用例位置 | 已編寫對應 pytest 用例時補充 |

---

## 嚴重性分級

| 標識 | 級別 | 判定標準 | 典型表現 |
|------|------|---------|---------|
| 🔴 | 嚴重 | 導致程序崩潰、資料丟失/損壞、核心功能完全不可用、安全漏洞 | OOM Kill、訊息無法傳送、模組無法載入、熱重載失敗 |
| 🟡 | 中等 | 功能異常但有避開路徑、非核心功能失效、偶發問題 | 狀態判斷錯誤、重複觸發、快取過期、錯誤提示不准 |
| 🟢 | 輕微 | 不影響核心功能、僅程式碼品質或體驗問題、潛在風險未爆發 | 棄用 API、死程式碼、缺失 warning 日誌 |

---

## 類型分類

| 類型 | 覆蓋範圍 |
|------|---------|
| 配置系統 | `ConfigManager`、配置讀寫、配置 Schema、熱更新 |
| 事件系統 | `Event` 模組（command/message/notice/request/meta）、事件分發、處理器註冊 |
| 適配器 | `AdapterManager`、`BaseAdapter`、帳戶解析、Bot 狀態、中間件 |
| 路由 | `RouterManager`、HTTP/WebSocket/SSE 路由、限流、CORS |
| 客戶端 | `HttpClient`、`ClientWebSocket`、aiohttp 封裝 |
| 存儲 | `StorageManager`、SQLite、SQL 構建器、嵌套鍵 |
| 加載系統 | `Loader`、`LazyModule`、`ModuleInitializer`、嚴格模式、模組發現 |
| CLI | `epsdk` 命令、`init`/`run`/`install`、參數解析、訊號處理 |
| 運行時 | `sdk.run`/`restart`/`uninit`、生命週期、訊號、子進程 |

---

## 條目範本

新增 Bug 條目請遵循以下格式：

```markdown
### [BUG-XXX] 標題

**問題**: 問題描述（錯誤訊息或典型現象）
**原因**: 根因分析
**影響版本**: 引入版本 - 修復版本
**修復版本**: x.x.x
**修復內容**: 修復方案
**修復日期**: YYYY/MM/DD

<!-- 可選字段 -->
**重現步驟**: （複雜 Bug 建議補充）
**關聯**: （Issue/PR 鏈接）
**回歸測試**: （驗證用例路徑）

**嚴重性**: 🔴 嚴重 | 🟡 中等 | 🟢 輕微
**類型**: 配置系統 / 事件系統 / 適配器 / 路由 / 客戶端 / 存儲 / 加載系統 / CLI / 運行時
```

---

## 統計概覽

| 嚴重性 | 數量 |
|--------|------|
| 🔴 嚴重 | 16 |
| 🟡 中等 | 13 |
| 🟢 輕微 | 2 |
| **合計** | **31** |

| 類型 | 數量 |
|------|------|
| 適配器 | 6 |
| 配置系統 | 7 |
| 事件系統 | 5 |
| CLI | 3 |
| 存儲 | 3 |
| 加載系統 | 4 |
| 路由 | 2 |
| 客戶端 | 1 |
| 運行時 | 1 |

> 注：單條 Bug 可歸屬多個類型，上表按主類型統計。

---

## 已修復的 Bug

### [BUG-001] 事件處理器重複註冊導致事件被多次處理

**問題**: 使用多個 `@message` / `@notice` 等裝飾器註冊處理器時，同一事件會被重複觸發多次，導致命令被執行多遍、日誌重複輸出。

**原因**: `BaseEventHandler` 向適配器事件總線註冊處理器時缺少去重邏輯，每個裝飾器都會向總線掛載一次，事件分發時被多次調用。

**影響版本**: 2.2.0-dev.0 - 2.2.1-dev.0

**修復版本**: 2.2.1-dev.0

**修復內容**: 優化 `BaseEventHandler`，確保每個事件類型只向適配器註冊一次處理器，避免重複觸發。

**修復日期**: 2025/08/18

**嚴重性**: 🔴 嚴重

**類型**: 事件系統

---

### [BUG-002] Init 命令適配器配置路徑類型錯誤

**問題**: 使用 `ep init` 命令進行交互式初始化時，選擇配置適配器會出現類型錯誤：

```
交互式初始化失敗: unsupported operand type(s) for /: 'str' and 'str'
```

**原因**: 2.3.7 版本調整配置檔案路徑時，方法參數類型不一致。`_configure_adapters_interactive_sync` 接收 `str` 類型參數，但內部使用 `Path` 的 `/` 操作符拼接路徑。

**影響版本**: 2.3.7 - 2.3.9-dev.1

**修復版本**: 2.3.9-dev.1

**修復內容**: 將 `_configure_adapters_interactive_sync` 方法的參數類型從 `str` 改為 `Path`，呼叫時直接傳遞 `Path` 對象。

**修復日期**: 2026/03/23

**嚴重性**: 🟡 中等

**類型**: CLI

---

### [BUG-003] 重啟後命令事件失效

**問題**: 呼叫 `sdk.restart()` 後，透過 `@command` 註冊的命令無法被觸發，表現為發送命令後機器人無回應。

**原因**: `adapter.shutdown()` 清空事件總線後，`BaseEventHandler` 的 `_linked_to_adapter_bus` 狀態未重置為 `False`，導致 `_process_event` 方法認為已經掛載到適配器總線，跳過重新掛載操作。

**影響版本**: 2.2.x - 2.4.0-dev.2

**修復版本**: 2.4.0-dev.3

**修復內容**: 引入 `_linked_to_adapter_bus` 狀態追蹤，`_clear_handlers()` 斷開總線連接後，下次 `register()` 自動重新掛載，適配 shutdown/restart 場景。

**修復日期**: 2026/04/09

**嚴重性**: 🔴 嚴重

**類型**: 事件系統

---

### [BUG-004] 生命週期事件處理器未清理

**問題**: `sdk.restart()` 後，舊的生命週期事件處理器仍然存在並重複觸發，導致同一個事件被多次處理。

**原因**: `lifecycle._handlers` 字典在 `uninit()` 時從未被清理，restart 後舊處理器與新處理器同時存在。

**影響版本**: 2.3.0 - 2.4.0-dev.2

**修復版本**: 2.4.0-dev.3

**修復內容**: 在 `Uninitializer` 的清理流程末尾（所有事件提交之後），清空 `lifecycle._handlers`。

**修復日期**: 2026/04/09

**嚴重性**: 🟡 中等

**類型**: 運行時

---

### [BUG-005] Event.is_friend_add/is_friend_delete 的 detail_type 與 OB12 標準不一致

**問題**: `Event.is_friend_add()` 檢查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 檢查 `detail_type == "friend_delete"`，但 OneBot12 標準定義的 `detail_type` 值為 `"friend_increase"` 和 `"friend_decrease"`。與 `notice.py` 中 `on_friend_add`/`on_friend_remove` 裝飾器使用的值不一致，導致透過裝飾器註冊的處理器觸發時，對應的 `is_friend_add()`/`is_friend_delete()` 判斷方法返回 `False`。

**原因**: `wrapper.py` 中使用了非標準的命名，而 `notice.py` 使用了正確的 OB12 標準命名。

**影響版本**: 實裝至今

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `is_friend_add()` 的匹配值從 `"friend_add"` 改為 `"friend_increase"`，`is_friend_delete()` 從 `"friend_delete"` 改為 `"friend_decrease"`。

**修復日期**: 2026/04/13

**嚴重性**: 🟡 中等

**類型**: 事件系統

---

### [BUG-006] adapter.clear() 未清理 _started_instances 導致重啟後狀態不正確

**問題**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、處理器和 `_bots`，但遺漏了 `_started_instances` 集合。如果適配器正在運行時呼叫 `clear()`，`_started_instances` 會保留懸空引用，導致重啟後狀態判斷錯誤。

**原因**: 2.4.0-dev.1 引入 `_started_instances` 時未在 `clear()` 中同步清理。

**影響版本**: 2.4.0-dev.1 - 2.4.2-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 在 `clear()` 方法中添加 `self._started_instances.clear()`。

**修復日期**: 2026/04/13

**嚴重性**: 🟡 中等

**類型**: 適配器

---

### [BUG-007] command.wait_reply() 使用已棄用的 asyncio.get_event_loop()

**問題**: `CommandHandler.wait_reply()` 方法使用 `asyncio.get_event_loop()` 創建 future 和獲取時間戳，該方法在 Python 3.10+ 中已棄用，在異步上下文中應使用 `asyncio.get_running_loop()`。與同文件中 `wrapper.py` 的 `wait_for()` 方法使用的 `get_running_loop()` 不一致。

**原因**: 開發時使用了舊版 API，後續新增的 `wait_for()` 使用了正確的 API 但未回溯修復舊程式碼。

**影響版本**: 2.3.0-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `command.py` 中兩處 `asyncio.get_event_loop()` 替換為 `asyncio.get_running_loop()`。

**修復日期**: 2026/04/13

**嚴重性**: 🟢 輕微

**類型**: 事件系統

---

### [BUG-008] Bot 離線事件在 shutdown 過程中被重複提交

**問題**: 呼叫 `adapter.shutdown()` 關閉所有適配器時，`_update_bot_status()` 會在關閉流程中反覆提交 Bot 離線事件，導致同一批 Bot 被多次標記離線並觸發多次 `adapter.bot.offline` 生命週期事件。

**原因**: 2.4.0-dev.1 引入的 Bot 狀態追蹤系統未在 `shutdown()` 期間設置"正在關閉"標誌，`_update_bot_status()` 無法區分正常離線與關閉流程中的級聯離線。

**影響版本**: 2.4.0-dev.1 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.1

**修復內容**: 在 `AdapterManager` 中新增 `_is_being_shutdown` 標誌，`shutdown()` 開始時置為 True、結束時清除；`_update_bot_status()` 檢查該標誌後跳過關閉過程中的重複提交。

**修復日期**: 2026/04/21

**嚴重性**: 🟡 中等

**類型**: 適配器

---

### [BUG-009] LazyModule 同步存取 BaseModule 導致未初始化完成

**問題**: 用戶在同步上下文中存取懶加載的 BaseModule 屬性時，模組使用 `loop.create_task()` 異步初始化但不等待，導致屬性存取時可能未初始化完成，引發競爭條件。

**原因**: `_ensure_initialized()` 對 BaseModule 使用 `loop.create_task(self._initialize())` 後立即返回，未確保初始化完成。

**影響版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**: 在同步上下文中，BaseModule 的初始化改為使用 `asyncio.run(self._initialize())`，確保初始化完成後再返回。保持透明代理特性，用戶無需感知同步/異步差異。

**修復日期**: 2026/04/21

**嚴重性**: 🟡 中等

**類型**: 加載系統

---

### [BUG-010] 配置系統多執行緒寫入導致資料丟失

**問題**: 在多執行緒環境下，多個執行緒同時呼叫 `config.setConfig()` 時，`_flush_config()` 讀取-修改-寫入操作不是原子性的，可能導致部分寫入丟失。

**原因**: `_flush_config()` 雖然使用了 `RLock`，但檔案讀取和寫入之間沒有檔案鎖保護，且 `_schedule_write` 的 Timer 可能被多次觸發導致覆蓋。

**影響版本**: 2.3.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**:
1. 新增檔案鎖機制（`_file_lock`）確保檔案操作原子性
2. 使用暫存檔案寫入後原子性重命名（`os.replace`/`os.rename`）
3. 改進 `_schedule_write` 的 Timer 取消和重新調度邏輯

**修復日期**: 2026/04/21

**嚴重性**: 🔴 嚴重

**類型**: 配置系統

---

### [BUG-011] Windows 下 CTRL+C 無法停止程式

**問題**: 在 Windows 上直接運行 `python main.py` 時，按下 CTRL+C 無法終止程式。程式正常啟動並輸出路由伺服器資訊後，CTRL+C 完全無反應，只能透過任務管理器強制殺死進程。而透過 `epsdk run` 啟動時可以正常停止——但 `epsdk run` 是透過子進程模型運行的。

**原因**: Hypercorn ASGI 伺服器的 `serve()` 函數內部透過 `signal.signal(SIGINT, handler)` 註冊了自己的 SIGINT 處理器，覆蓋了 Python 預設的 `KeyboardInterrupt` 處理機制。當透過 `asyncio.create_task()` 啟動 Hypercorn 作為背景任務時，Hypercorn 的內部 shutdown 流程無法正常觸發（因為它期望的是 `worker_serve` 模式），導致 CTRL+C 訊號被 Hypercorn 吞掉但不會引發任何清理動作。

**影響版本**: 2.3.6 - 2.4.2

**修復版本**: 2.4.3-dev.0

**修復內容**:
1. 將 ASGI 伺服器從 Hypercorn 切換為 Uvicorn（`pyproject.toml` 依賴變更）
2. 使用 `uvicorn.Server._serve()` 直接啟動伺服器，**繞過** `capture_signals()` 訊號處理上下文管理器
3. 透過 `server.should_exit = True` 實現優雅停止，超時則取消背景任務
4. 同步移除子進程運行模型和 `runtime/cleanup.py` 清理模組（子進程清理機制不再需要）

**修復日期**: 2026/04/28

**嚴重性**: 🔴 嚴重

**類型**: CLI / 運行時

---

### [BUG-012] 熱重啟後已更新模組的 Python 程式碼未生效

**問題**: 執行 `sdk.restart()` 軟重啟後，已透過 `epsdk install` 升級的模組/適配器的新程式碼（如新增 API 路由）不生效，仍運行舊版本邏輯。必須完全重啟進程才能加載最新程式碼。

**原因**: `_do_restart()` 在重新初始化時呼叫 `entry_point.load()`，但該函數從 `sys.modules` 返回了快取的舊版本模組物件，而非從磁盤重新加載。

**影響版本**: 早期版本 - 2.4.3-dev.1

**修復版本**: 2.4.3-dev.1

**修復內容**: 在 `uninit()` 後、`init()` 前清理 `sys.modules` 中已加載模組/適配器包的快取，使 `entry_point.load()` 從磁盤加載最新程式碼。新增 `_collect_top_level_modules()` 與 `_invalidate_module_cache()` 輔助方法，透過 `top_level.txt` 或 entry-point value 推導頂層模組名。

**修復日期**: 2026/05/03

**嚴重性**: 🔴 嚴重

**類型**: 加載系統 / 運行時

---

### [BUG-013] 模組加載策略排序邏輯錯誤

**問題**: `ModuleLoadStrategy` 提供了 `priority` 字段用於聲明模組的初始化優先級，但加載策略的實現存在失誤，導致模組未按預期的優先級順序初始化，實際按 `entry_points()` 的預設順序加載。當模組間存在加載依賴時，無法透過 `priority` 確保正確的初始化先後關係。

**原因**: 加載策略的實現中排序邏輯有誤，`initialize_modules()` 未使用 `priority` 對模組列表進行排序。

**影響版本**: 2.3.4 - 2.4.5-dev.2

**修復版本**: 2.4.5-dev.3

**修復內容**: 在 `initialize_modules()` 遍歷前，按 `priority` 降序排序模組列表。同 priority 的模組保持原有相對順序（穩定排序）。

**修復日期**: 2026/05/15

**嚴重性**: 🟡 中等

**類型**: 加載系統

---

### [BUG-014] 適配器中間件返回 None 導致事件資料丟失

**問題**: `adapter.emit()` 在執行 OneBot12 中間件鏈時，如果某個中間件返回 `None`（例如忘記 `return data`），後續中間件和所有事件處理器收到的 `processed_data` 變為 `None`，導致事件處理完全失效。

**原因**: 中間件鏈的實現 `processed_data = await middleware(processed_data)` 未檢查返回值是否為 `None`，直接覆蓋了上一步的處理結果。

**影響版本**: unknown - 2.4.5-dev.3

**修復版本**: 2.4.5-dev.4

**修復內容**: 中間件返回 `None` 時忽略該返回值，保留原資料繼續傳遞，並輸出 warning 級別日誌。

**修復日期**: 2026/05/15

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 事件系統

---

### [BUG-015] 配置檔案路徑依賴工作目錄

**問題**: `ConfigManager` 的配置檔案路徑預設為相對路徑 `"config/config.toml"`，在運行時依賴 `os.getcwd()` 解析。如果工作目錄在運行期間發生變化（例如透過 `os.chdir()`），配置檔案的讀寫操作會指向錯誤的位置，導致配置丟失或讀取到舊資料。

**原因**: `__init__` 中直接儲存相對路徑，未在初始化時將其解析為絕對路徑。

**影響版本**: 2.3.7 - 2.4.5-dev.3

**修復版本**: 2.4.5-dev.4

**修復內容**: 在 `ConfigManager.__init__()` 中，如果傳入的路徑為相對路徑，自動透過 `os.path.abspath()` 解析為絕對路徑。

**修復日期**: 2026/05/15

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-016] BaseStorage 將儲存值 None 與鍵不存在混淆

**問題**: `BaseStorage.get_multi()` / `__getattr__()` 無法區分"鍵不存在"與"鍵的值就是 `None`"兩種情況，使用者顯式存入 `None` 後再讀取時會被當作鍵不存在處理。

**原因**: 取值邏輯直接用 `value is None` 判斷鍵是否存在，缺少獨立的"缺失"標記。

**影響版本**: 早期版本 - 2.4.6-dev.6

**修復版本**: 2.4.6-dev.6

**修復內容**: 引入 `_SENTINEL` 哨兵值區分"鍵不存在"與"值為 None"，二者不再混淆。

**修復日期**: 2026/06/07

**嚴重性**: 🟡 中等

**類型**: 存儲

---

### [BUG-017] WebSocket 路由 auto_accept 標誌在服務重啟後丟失

**問題**: 服務重啟（如 `sdk.restart()`）後，所有 WebSocket 路由的 `auto_accept` 配置都變回 `False`，原本期望自動 accept 的連接變為掛起狀態，客戶端長時間收不到回應，表現為 WS 連接卡死。

**原因**: `_restore_routes_from_records()` 在從持久化記錄恢復路由時把 `auto_accept` 硬編碼為 `False`，未讀取原始記錄中的值；同時路由儲存元組也從二元組擴展為三元組時未同步更新恢復邏輯。

**影響版本**: 2.3.8-dev.0 - 2.4.6-dev.6

**修復版本**: 2.4.6-dev.6

**修復內容**: 路由儲存元組擴展為 `(handler, auth_handler, auto_accept)`，`_restore_routes_from_records()` 從記錄讀取真實 `auto_accept` 值而非硬編碼 `False`。

**修復日期**: 2026/06/07

**嚴重性**: 🔴 嚴重

**類型**: 路由

---

### [BUG-018] HTTP/WS 客戶端併發呼叫導致崩潰與連接遺漏

**問題**: `Core/client.py` 的 HTTP 與 WebSocket 客戶端在併發場景下存在多個穩定性缺陷，會導致連接遺漏或進程崩潰：
- 多協程併發呼叫 `ClientWebSocket.receive()` 時 aiohttp 抛出 `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` 併發呼叫可能創建多個 session 且 `_drain_sessions()` 未關閉舊連接，造成連接遺漏
- `request()` 的異常捕獲順序錯誤：`except ClientConnectionError`（ErisPulse 異常）永不觸發，aiohttp 的連接錯誤被通用 `except Exception` 接住，導致"連接重試 + session 重建"邏輯（死程式碼）從未執行
- `send_json()` 忽略 `mode="binary"` 參數；`_get_ws_session()` 未傳入預設請求頭

**原因**: 客戶端初次實現（2.4.6-dev.5）缺少併發保護與異常分類，對 aiohttp 異常體系與 ErisPulse 自定義異常的繼承關係處理不當。

**影響版本**: 2.4.6-dev.5 - 2.4.8

**修復版本**: 2.4.8

**修復內容**:
1. 新增 `_recv_lock` 序列化所有 `receive()` / `receive_text()` / `receive_bytes()` 調用
2. 新增 `_session_lock` 保護 session 創建；`_drain_sessions()` 改為異步方法並真正關閉舊 session
3. 重構 `request()` 異常捕獲順序：`asyncio.TimeoutError` → `aiohttp.ClientConnectionError`（觸發 session 重建）→ `aiohttp.ClientError` → `ClientError`（透傳）→ `Exception`
4. 修復 `send_json()` 的 mode 處理、`_get_ws_session()` 預設請求頭透傳、`close()` 的併發競爭、`HttpResponse.__aexit__` 重複 `release()`

**修復日期**: 2026/06/12

**嚴重性**: 🔴 嚴重

**類型**: 客戶端

---

### [BUG-019] 適配器熱重載時路由衝突導致重載失敗

**問題**: 第三方模組（如 Dashboard）觸發適配器熱重載，或適配器啟動失敗重試時，因上次註冊的舊路由（如 `onebot11_default`）未清理，抛出 `WebSocket路徑 ... 已註冊` 衝突，導致重載失敗。需要完全重啟進程才能恢復。

**原因**: `AdapterManager.shutdown()` 僅以 `unregister_all_by_namespace(platform)` 清理路由，但適配器（如 OneBot11）以 `onebot11_{account_name}` 為命名空間註冊 WS 路由，顆粒度不匹配導致清理為空操作；啟動失敗重試路徑也未清理上次殘留路由。

**影響版本**: 早期版本 - 2.4.9

**修復版本**: 2.4.9

**修復內容**:
1. 路由註冊時透過 `current_owner` ContextVar 自動追蹤 `owner → namespace` 歸屬關係
2. 新增 `unregister_all_by_owner(owner)`，停止/重啟時同時按 owner 清理，覆蓋細顆粒度命名空間
3. 新增 `_stop_adapter(platform)` 原語（"停止即清理"），將停止適配器與回收其註冊的資源綁定在一次呼叫裡，`restart()` 和啟動失敗重試均經此入口
4. 新增框架級 `adapter.restart(platform)` API，第三方模組應呼叫此方法而非直接操作適配器實例

**修復日期**: 2026/06/12

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 路由

---

### [BUG-020] 子進程模式 `ep run <script>` 找不到腳本所在目錄的子包

**問題**: 使用 `ep r .\main.py` 非熱重載模式運行腳本時，如果腳本有相對導入（如 `from qg import ...`），會報 `No module named 'qg'` 錯誤。而 `--reload` 模式可以正常運行。

**原因**: 非熱重載模式直接呼叫 `runpy.run_path()` 執行腳本，該函數不會自動將腳本所在目錄加入 `sys.path`。而 `--reload` 模式透過 `subprocess.Popen` 子進程運行，子進程自動繼承當前工作目錄，`sys.path[0]` 即為腳本所在目錄，所以能正常工作。

**影響版本**: 2.5.0 - 2.5.2-dev.0

**修復版本**: 2.5.2-dev.0

**修復內容**: 在 `runpy.run_path()` 呼叫前，手動將腳本所在目錄插入 `sys.path[0]`。

**修復日期**: 2026/06/27

**嚴重性**: 🟡 中等

**類型**: CLI

---

### [BUG-021] SQL 查詢建構器拒絕合法通配符和列表達式

**問題**: `SQLiteQueryBuilder` 的 `_build_select_sql()` 對所有 SELECT 列呼叫 `_validate_identifier()`，該函數使用嚴格的白名單正則 `^[a-zA-Z_][a-zA-Z0-9_]*$`，導致合法 SQL 語法被誤判為不安全列名：

- `SELECT *` — `*` 是 SQL 標準通配符
- `SELECT COUNT(*)` — 聚合函數
- `SELECT users.name` — 限定列名
- `SELECT col AS alias` — 列別名

其中 `Select("*")` 被 Cron 等模組使用，導致模組 `on_load` 執行失敗，模組無法加載。

**原因**: 2.4.6 版本增強了 SQL 注入防護，引入了 `_validate_identifier()` 白名單校驗。該校驗應用於所有列名，但未區分讀取端（SELECT/ORDER BY）和寫入端（INSERT/UPDATE）。SELECT 列允許複雜的 SQL 表達式，不應受簡單標識符白名單限制。

**影響版本**: 2.4.6 - 2.5.2-dev.1

**修復版本**: 2.5.2-dev.2

**修復內容**: 將 SELECT/ORDER BY 的列校驗從白名單模式改為黑名單模式：
1. 新增 `_validate_select_column()` 函數，僅攔截 SQL 注入危險字元（`;` `'` `"` `--` `/*` `*/` `\x00` 換行符）
2. 允許任意合法 SQL 列表達式（`*`、`table.*`、`table.column`、`COUNT(*)`、`col AS alias` 等）
3. INSERT/UPDATE 列名仍保持嚴格白名單校驗（僅允許簡單標識符）

**修復日期**: 2026/06/29

**嚴重性**: 🔴 嚴重

**類型**: 存儲

---

### [BUG-022] _resolve_account() 帳戶解析回歸（_accounts_data 未填補）

**問題**: 2.5.2 配置系統重構後，聲稱了 `AccountConfigClass` 的多帳戶適配器在呼叫 `wait_reply`、`reply` 等需要傳送訊息的方法時，抛錯 `ValueError("未聲稱 AccountConfigClass，無法解析帳戶")`。即使適配器正確配置了多帳戶資訊，帳戶解析仍然失敗。

**原因**: 2.5.2-dev.5 將 `_load_accounts()`（負責讀取配置 + 校驗 + 填補 `_accounts_data`）重構為 `_ensure_accounts_exist()`（僅生成配置範本），但 `_resolve_account()` 仍檢查 `self._accounts_data is None`。由於 `_ensure_accounts_exist()` 不再填補 `_accounts_data`，該屬性始終為 `None`，導致 `_resolve_account()` 提前返回 `(None, None)`，帳戶解析完全失效。

**根因鏈路**:
```
_load_accounts() 被刪除
  → __init__ 不再填補 _accounts_data
    → _accounts_data 恆為 None
      → _resolve_account() 檢查 _accounts_data is None → return (None, None)
        → 下游呼叫 _resolve_account 的地方（如 call_api）拿到 None
          → 觸發拋錯
```

**影響版本**: 2.5.2-dev.5 - 2.5.2

**修復版本**: 2.5.3

**修復內容**: 在 `BaseAdapter.__init__` 中，`_ensure_accounts_exist()` 之後恢復 `_accounts_data` 的填補：
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # 恢復填補，資料源為實時讀取的 accounts 屬性
```
`_resolve_account()` 逻辑保持不變，完全向後相容：
- 不聲稱 `AccountConfigClass` 的適配器：`_accounts_data` 保持 `None` → 回傳 `(None, None)`
- 聲稱了 `AccountConfigClass` 的適配器：`_accounts_data` 被填補 → 正常解析
- 覆寫 `_load_accounts` 或手動設定 `_accounts_data` 的適配器：在 `super().__init__()` 後覆蓋，優先級最高

**修復日期**: 2026/07/07

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 配置系統

---

### [BUG-023] 修改帳戶配置後適配器快取未刷新導致帳戶解析失敗

**問題**: 用戶透過 Dashboard 修改多帳戶適配器的帳戶配置（如填寫 token）後，適配器仍使用舊快取，呼叫傳送訊息相關方法时报 `未找到可用帳戶 (account_id=default)`。必須重啟進程才能讓新配置生效。

**原因**: `_accounts_data` 僅在 `BaseAdapter.__init__` 時從配置儲存讀取一次，之後不再刷新。`AdapterManager._run_adapter()` 與 `restart()` 在呼叫 `adapter.start()` 前未重新讀取帳戶配置，導致快取與實際配置脫節。

**影響版本**: 2.4.6 - 2.5.4

**修復版本**: 2.5.4

**修復內容**: 在 `AdapterManager._run_adapter()` 和 `restart()` 中，呼叫 `adapter.start()` 之前刷新 `adapter._accounts_data = adapter.accounts`，確保每次啟動時使用最新配置。

**修復日期**: 2026/07/09

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 配置系統

---

### [BUG-024] storage.set() 寫入大數字 ID 鍵時觸發 OOM Kill

**問題**: 呼叫 `storage.set()` 寫入包含大純數字段（如 QQ 群號 `871684833`）的嵌套鍵路徑時，進程被容器 OOM Kill（退出碼 -9），服務直接崩潰無法恢復。

**原因**: `_set_nested_value` 的遞迴實現中，嵌套鍵路徑裡的純數字段被 `isdigit()` 誤判為列表索引，觸發 `current.extend([None] * (index - len(current) + 1))`，試圖分配數億元素的列表，瞬間耗盡記憶體。

**根因鏈路**:
```
鍵路徑包含純數字段（如群號 871684833）
  → isdigit() 誤判為陣列索引
    → extend([None] * (871684833 - len(current) + 1))
      → 試圖分配數億元素
        → 記憶體耗盡 → 容器 OOM Kill（退出碼 -9）
```

**影響版本**: 2.5.1 - 2.5.5

**修復版本**: 2.5.5

**修復內容**:
1. 預創建中間層時始終使用字典，不再根據下一段是否為數字猜測容器類型
2. 設定最終值時，僅當容器本身已是列表且索引小於 `STORAGE_MAX_LIST_INDEX`（10000）時才按索引處理，超大索引安全跳過
3. 將遞迴實現改為迭代實現，消除原程式碼中潛在的無限遞迴風險
4. 新增 `STORAGE_MAX_LIST_INDEX` 常量到 `Core/constants.py`，集中管理索引安全上限

**修復日期**: 2026/07/10

**重現步驟**:
```python
# 寫入包含大數字段（如 QQ 群號）的嵌套鍵路徑即可觸發
await sdk.storage.aset("groups.871684833.name", "某群")
# → 進程記憶體瞬間飆升，被 OOM Kill
```

**回歸測試**: `tests/unit/test_unit_storage.py` 新增 4 個回歸用例
- `test_nested_key_numeric_segment_as_dict_key` — 精確重現 OOM 場景
- `test_nested_key_numeric_segment_multiple` — 多個連續數字段均作為字典鍵
- `test_nested_key_existing_list_index_set_within_limit` — 已有列表合理索引寫入
- `test_nested_key_list_index_safety_limit` — 超大索引安全限制驗證

**嚴重性**: 🔴 嚴重

**類型**: 存儲

---

### [BUG-025] on_config_update 回調未被核心路由

**問題**: `on_config_update(old, new)` 回調在基類（`BaseModule` / `BaseAdapter`）中已定義，但框架核心未將其與配置變更事件關聯。實際表現：透過配置管理介面改配置時可以觸發，而手動編輯 `config.toml` 或程式碼呼叫 `setConfig()` 時不會觸發 `on_config_update`。

**原因**: `ConfigManager` 在配置變更時會發射 `config.set` / `config.updated` 生命週期事件，但缺少將這些事件轉發到各組件 `on_config_update` 方法的訂閱邏輯。

**根因鏈路**:
```
核心未訂閱 config.set / config.updated
  → 配置變更事件無轉發
    → on_config_update 未被呼叫
      → 手動編輯檔案 / 程式碼 setConfig 不觸發熱更新回調
```

**影響版本**: 全版本

**修復版本**: 2.6.2

**修復內容**: `ModuleManager` / `AdapterManager` 訂閱 `config.set`（覆蓋程式碼 `setConfig()` 路徑）與 `config.updated`（覆蓋手動編輯檔案路徑）事件訂閱，按配置鍵前綴匹配後呼叫對應組件的 `on_config_update`，傳入類型安全的配置物件。同時修復 `_flush_config()` 寫入檔案後未同步 `_config_mtime` 的問題，避免框架自身寫入被檔案監聽任務誤判為外部修改而重複觸發 `config.updated`。

**相容性說明**: 配置熱更新現由框架核心統一維護。此前由配置管理介面代為觸發的邏輯已移除，升級框架後需同步升級配置管理介面，否則會出現重複觸發（核心 + 介面各呼叫一次）。`on_config_update` 方法簽名與語義保持不變，子類無需修改。

**修復日期**: 2026/07/23

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-026] notice/request 事件 reply 目標推斷錯誤

**問題**: 在群通知事件（如成員加群 `group_member_increase`）中呼叫 `event.reply()`，訊息被發送到觸發事件的用戶私聊，而非事件所在的群。好友通知事件同理，回覆目標可能錯亂。

**原因**: `infer_receive_type()` 將事件的 `detail_type` 直接當作會話類型回傳。對於 message 事件這是正確的（`detail_type` 值 `private`/`group` 即會話類型），但 notice/request 事件的 `detail_type` 是語義子類型（如 `group_member_increase`、`friend_increase`），不是會話類型。後續的 `convert_to_send_type()` 和 `get_id_field()` 在映射表中找不到該值，回退到預設的 `"user"` / `"user_id"`，導致回覆目標錯亂。

**根因鏈路**:
```
notice 事件 detail_type="group_member_increase"
  → infer_receive_type() 直接回傳 "group_member_increase"
    → convert_to_send_type("group_member_increase") 不在映射表 → 回退 "user"
    → get_id_field("group_member_increase") 不在映射表 → 回退 "user_id"
      → target_id = event["user_id"]  ← 新成員私聊（而非群）
```

**影響版本**: 全版本

**修復版本**: 2.7.0-dev.3

**修復內容**: `infer_receive_type()` 增加判斷——`detail_type` 只有在是已知會話類型（標準類型或自定義類型）時才直接回傳；否則根據 ID 字段（`group_id` / `channel_id` / `user_id` 等）推斷正確的會話類型。

**回歸測試**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference`（10 用例）

**修復日期**: 2026/07/29

**嚴重性**: 🟢 輕微

**類型**: 事件系統

---

### [BUG-027] 路由限流清理任務使用固定窗口導致長窗口限流規則失效

**問題**: 將路由限流配置為長窗口規則（如 `100/hour`、`{"requests": 100, "window": 3600}`）時，限流形同虛設——實際表現近似 `100/minute`（每小時可放過至約 6000 次請求），完全無法起到預期的小時級防護作用。

**原因**: `_apply_rate_limit` 解析得到每路由的實際 `window`（最高 3600 秒），per-request 檢查也確實使用該窗口；但後台清理任務 `_cleanup_expired_rate_limits` 卻用固定常量 `DEFAULT_RATE_LIMIT_WINDOW_SECS`（60 秒）作為**所有**路由的統一清理閾值。於是 `100/hour` 路由中早於 60 秒的時間戳被清理任務提前清除，小時窗口內永遠累積不到接近 100 條記錄，限流被嚴重削弱。

**根因鏈路**:
```
_apply_rate_limit 解析 window=3600（100/hour）
  → per-request 檢查按 3600s 保留時間戳（正確）
  → 但 _cleanup_expired_rate_limits 用固定 max_window=60s 清理
    → 60s 前的時間戳被全部清除
      → 小時窗口永遠只餘最近 1 分鐘的記錄
        → 100/hour 實際退化為 ~100/minute（放寬約 60 倍）
```

**影響版本**: 2.6.0-dev.0 - 2.7.0-dev.4

**修復版本**: 2.7.0-dev.5

**修復內容**: 新增 `_rate_limit_windows: dict[str, int]` 按 store key 記錄每路由實際窗口；`_apply_rate_limit` 首次創建條目時寫入窗口；`_cleanup_expired_rate_limits` 改為按各 key 自身窗口清理（缺失時回退預設值）；清理刪除條目與 `stop()` 時同步維護兩個字典。

**修復日期**: 2026/07/31

**回歸測試**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**嚴重性**: 🔴 嚴重

**類型**: 路由

---

### [BUG-029] 配置監聽任務廣播半成品 TOML 並靜默吞掉異常

**問題**: 用戶手動編輯 `config.toml` 保存到一半（產生瞬時的語法錯誤）時，配置監聽背景執行緒會檢測到 mtime 變化、重載配置，但加載失敗後仍以空配置 `{}` 發射 `config.updated` 事件，導致適配器/模組的 `on_config_update` 收到空配置、誤以為所有配置項被清空而回退預設值。此外監聽迴圈用 `except Exception: pass` 靜默吞掉所有異常，watcher 故障無從排查。

**原因**: 兩個缺陷疊加：
1. `_load_config` 在 TOML 語法錯誤/權限錯誤時把 `self._cache` 擦寫為 `{}`，但背景監聽執行緒 `_watch_loop` 與快取超時路徑 `_check_cache_validity` 都在呼叫 `_load_config()` 後**無條件**執行 `_emit_config_updated()`，把"加載失敗產生的空快取"當作真實變更廣播。
2. `_watch_loop` 的 `except Exception` 改為以 warning 級別記錄（新增 i18n 鍵 `core.config.watcher_error`，五語言同步）

**根因鏈路**:
```
用戶保存到一半 → TOML 語法錯誤
  → _load_config() 擦寫 _cache = {}
    → _watch_loop 無條件 _emit_config_updated(new_config={})
      → 適配器/模組 on_config_update 收到空配置
        → 誤判配置被清空，回退預設值
```

**影響版本**: 2.6.2-dev.1 - 2.7.0-dev.4

**修復版本**: 2.7.0-dev.5

**修復內容**:
1. `_load_config` 改為返回 `bool`；TOML 語法錯誤/權限/其他錯誤時**保留上次有效快取**（不再擦寫為 `{}`），僅記錄診斷日誌並返回 `False`
2. `_watch_loop` 與 `_check_cache_validity` 僅在 `_load_config()` 返回 `True` 時才發射 `config.updated`
3. `_watch_loop` 的 `except Exception` 改為以 warning 級別記錄（新增 i18n 鍵 `core.config.watcher_error`，五語言同步）

**修復日期**: 2026/07/31

**回歸測試**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`、`test_permission_denied_logs_clear_message`（更新為驗證保留快取 + 返回 False）

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-030] 配置 watcher 競態導致 setConfig 延遲寫入靜默丟資料

**問題**: 多個用戶報告使用 `config.setConfig(key, value)`（預設 `immediate=False`）後，自己的模組配置未寫入 `config.toml`，而其它模組的配置正常。設定 `immediate=True`（強制刷盤）可避開。表現為：運行期寫入的配置在下次重啟後丟失，啟動期範本生成的配置保留。

**原因**: 兩個疊加缺陷：
1. **邏輯缺陷**：`_watch_loop` 在 `_check_file_change()` 回傳 `True` 時無條件 `_dirty_keys.clear()` 丟失所有待寫鍵。但 `_check_file_change()` 僅用 `!=` 對比 mtime，框架自身的 `_flush_config` 寫盤也會改變 mtime——雖然 `_flush_config` 在寫盤後更新 `_config_mtime`，但 watcher 線程在檔案寫入與 mtime 賦值之間（以及粗粒度檔案系統上）仍可能觀測到 mtime 差值，誤判為"外部修改"並清空全部待寫鍵。
2. **執行緒缺陷**：`_watch_loop` 操作 `_write_timer`/`_dirty_keys` 時未持有 `_lock`，與 `setConfig`（持鎖寫 `_dirty_keys`）、`_schedule_write`（持鎖寫 `_write_timer`）存在資料競爭。

**根因鏈路**:
```
模組A setConfig(immediate=True) → flush 寫盤，mtime 變化
  → 用戶模組 setConfig(immediate=False) → 進入 _dirty_keys，5s 後刷盤
    → watcher 輪詢，_check_file_change 觀測到先前自身寫入的 mtime 差值
      → _dirty_keys.clear() → 用戶模組的待寫鍵被靜默丟棄
        → 重啟後配置缺失
```

**影響版本**: 2.6.0 - 2.7.0

**修復版本**: 2.7.1

**修復內容**:
1. 新增 `_last_self_write_mtime` 字段，`_flush_config` 寫盤後同步記錄；`_check_file_change` 在 mtime 變化時先對比該值，匹配則判定為自身寫入回傳 `False`
2. `_watch_loop` 整段持 `_lock`；真正外部修改時保留 `_dirty_keys`（merge 語義），下次 flush 與外部內容合併（臟鍵優先），不再 `clear()`
3. `getConfig`/`_check_cache_validity` 路徑不受影響（其 reload 本就不清臟鍵）

**修復日期**: 2026/08/06

**回歸測試**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`、`test_external_change_preserves_dirty_keys`、`test_flush_merges_dirty_with_external`

**嚴重性**: 🔴 嚴重

**類型**: 配置系統

---

### [BUG-031] 本地插件熱重載完全不可用（reload_plugin 恆回傳 False）

**問題**: 呼叫 `sdk.reload_plugin(name)` 或經 `sdk.enable_plugin_hot_reload()` 檔案監控觸發重載時，日誌輸出 WARNING「熱重載不可用：SDK 尚未初始化模組加載器」並回傳 `False`——即使框架已正常初始化、插件已從 `plugins/` 加載，熱重載功能在真實運行路徑上完全失效。

**原因**: `ModuleLoader` 僅作為 `Initializer` 的內部屬性創建（`Initializer.__init__` 中的 `self._module_loader`），從未注入 SDK 實例；而 `sdk.reload_plugin()` 檢查並讀取的是 SDK 實例上的 `self._module_loader`（恆為 None）。此外同方法還向加載器傳遞了 SDK 上不存在的 `self._sdk` 屬性（第二個潛伏斷點，修復第一處後必然觸發 `AttributeError`）。

**影響版本**: 2.8.0-dev.0 - 2.8.0-dev.1

**修復版本**: 2.8.0-dev.1

**修復內容**:
1. `Initializer.__init__` 創建加載器後注入 `sdk_instance._module_loader = self._module_loader`（硬重啟重建 Initializer 時自動重新指向新加載器）
2. `uninit()` 重置階段同步清空 `sdk._module_loader`，避免卸載後經陳舊加載器重載
3. `reload_plugin` 改向加載器傳遞 SDK 實例自身（`self`）

**修復日期**: 2026/09/04

**回歸測試**: `tests/unit/test_unit_plugin_reload.py` → `TestSDKLoaderWiring`（注入接線 / 未初始化優雅 False / SDK 自身傳遞）

**嚴重性**: 🔴 嚴重

**類型**: 加載系統

---

### [BUG-033] 配置延遲刷盤期間「寫後立讀」讀到舊值

**問題**: `config.setConfig()`（預設 `immediate=False` 延遲約 5 秒刷盤）寫入點分鍵後，立即讀取其**父級/祖先節點**（如 `set_erispulse_section("scope.handlers.MyModule", {...})` 後呼叫 `get_erispulse_config()`）返回的是舊值，寫入的子鍵"消失"，直到刷盤後才可見。控制面作用域配置熱更新等"寫-讀-寫"場景受影響（2.8.0 測試插件 `/t_section` 用例暴露）。

**原因**: `setConfig` 將點分鍵以**扁平形式**存入待寫隊列 `_dirty_keys`，僅 `getConfig` 的**精確鍵查詢**命中待寫隊列；樹形路徑查詢（`getConfig("ErisPulse.scope")`）只走快取樹，不疊加待寫值——延遲刷盤（`_flush_config` 才將臟鍵合併進快取並清隊列）期間形成讀-你-寫斷層。

**影響版本**: 2.6.0 - 2.8.0-dev.1

**修復版本**: 2.8.0-dev.1

**修復內容**: `getConfig` 引入待寫疊加語義——① 精確命中待寫鍵直接回傳（原有行為不變）；② 待寫鍵是查詢鍵的祖先 → 取最長待寫祖先，在其值子樹內解析剩餘路徑；③ 待寫鍵是查詢鍵的後代 → 構建疊加子樹（`_dirty_overlay`）與快取子樹深合併（`_deep_merge`，override 优先，不修改原快取物件）。無待寫鍵時走原快路徑，零額外開銷。

**修復日期**: 2026/09/04

**回歸測試**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`、`test_get_config_overlay_merges_with_cache_siblings`、`test_get_config_overlay_new_branch`、`test_get_config_dirty_ancestor_query`、`test_get_config_dirty_exact_key_still_wins`

**嚴重性**: 🟡 中等

**類型**: 配置系統