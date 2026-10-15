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
| **問題** | Bug 的外在表現、用戶可觀察到的異常現象。盡量給出報錯資訊或典型場景 |
| **原因** | 根因分析，指向具體的代碼缺陷（含「根因鏈路」圖示用於複雜場景） |
| **影響版本** | 受影響的版本區間，格式 `引入版本 - 修復版本`（含兩端 dev 版本） |
| **修復版本** | 修復該 Bug 的具體版本號 |
| **修復內容** | 修復方案的簡要描述，含關鍵代碼變更點 |
| **修復日期** | 對應修復版本的發布日期，採用 `YYYY/MM/DD` 格式 |
| **嚴重性** | 按下文「嚴重性分級」標註 |
| **類型** | 按下文「類型分類」標註，可組合（如 `適配器 / 路由`） |

### 可選字段

| 字段 | 說明 | 適用場景 |
|------|------|---------|
| **復現步驟** | 觸發該 Bug 的最小可復現路徑 | 複雜 Bug、偶發性 Bug 建議補充 |
| **關聯** | 相關 Issue / PR / Commit 鏈接 | 有外部討論記錄時補充 |
| **回歸測試** | 驗證修復、防止再次回歸的測試用例位置 | 已編寫對應 pytest 用例時補充 |

---

## 严重性分级

| 标识 | 级别 | 判定标准 | 典型表现 |
|------|------|---------|---------|
| 🔴 | 严重 | 导致进程崩溃、数据丢失/损坏、核心功能完全不可用、安全漏洞 | OOM Kill、消息无法发送、模块无法加载、热重载失败 |
| 🟡 | 中等 | 功能异常但有规避路径、非核心功能失效、偶发问题 | 状态判断错误、重复触发、缓存过期、错误提示不准 |
| 🟢 | 轻微 | 不影响核心功能、仅代码质量或体验问题、潜在风险未爆发 | 弃用 API、死代码、缺失 warning 日志 |

---

## 类型分类

| 类型 | 覆盖范围 |
|------|---------|
| 配置系统 | `ConfigManager`、配置读写、配置 Schema、热更新 |
| 事件系统 | `Event` 模块（command/message/notice/request/meta）、事件分发、处理器注册 |
| 适配器 | `AdapterManager`、`BaseAdapter`、账户解析、Bot 状态、中间件 |
| 路由 | `RouterManager`、HTTP/WebSocket/SSE 路由、限流、CORS |
| 客户端 | `HttpClient`、`ClientWebSocket`、aiohttp 封装 |
| 存储 | `StorageManager`、SQLite、SQL 构建器、嵌套键 |
| 加载系统 | `Loader`、`LazyModule`、`ModuleInitializer`、严格模式、模块发现 |
| CLI | `epsdk` 命令、`init`/`run`/`install`、参数解析、信号处理 |
| 运行时 | `sdk.run`/`restart`/`uninit`、生命周期、信号、子进程 |

---

## 条目模板

新增 Bug 条目请遵循以下格式：

```markdown
### [BUG-XXX] 标题

**问题**: 问题描述（报错信息或典型现象）
**原因**: 根因分析
**影响版本**: 引入版本 - 修复版本
**修复版本**: x.x.x
**修复内容**: 修复方案
**修复日期**: YYYY/MM/DD

<!-- 可选字段 -->
**复现步骤**: （复杂 Bug 建议补充）
**关联**: （Issue/PR 链接）
**回归测试**: （验证用例路径）

**严重性**: 🔴 严重 | 🟡 中等 | 🟢 轻微
**类型**: 配置系统 / 事件系统 / 适配器 / 路由 / 客户端 / 存储 / 加载系统 / CLI / 运行时
```

---

## 統計概覽

| 嚴重性 | 數量 |
|--------|------|
| 🔴 嚴重 | 16 |
| 🟡 中等 | 19 |
| 🟢 輕微 | 3 |
| **合計** | **38** |

| 類型 | 數量 |
|------|------|
| 適配器 | 6 |
| 配置系統 | 12 |
| 事件系統 | 7 |
| CLI | 3 |
| 儲存 | 3 |
| 加載系統 | 3 |
| 路由 | 2 |
| 客戶端 | 1 |
| 運行時 | 1 |

> 注：單條 Bug 可歸屬多個類型，上表按主類型統計。  
> 注：BUG-028 / BUG-031 編號空缺（登記時廢棄，為保持既有編號穩定不回收重排）。

## 已修復的 Bug

### [BUG-001] 事件處理器重複註冊導致事件被多次處理

**問題**: 使用多個 `@message` / `@notice` 等裝飾器註冊處理器時，同一事件會被重複觸發多次，導致命令執行多遍、日誌重複輸出。

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
交互式初始化失敗: 不支援的運算元類型: 'str' 和 'str'
```

**原因**: 2.3.7 版本調整配置文件路徑時，方法參數類型不一致。`_configure_adapters_interactive_sync` 接收 `str` 類型參數，但內部使用 `Path` 的 `/` 操作符拼接路徑。

**影響版本**: 2.3.7 - 2.3.9-dev.1

**修復版本**: 2.3.9-dev.1

**修復內容**: 將 `_configure_adapters_interactive_sync` 方法的參數類型從 `str` 改為 `Path`，呼叫時直接傳遞 `Path` 對象。

**修復日期**: 2026/03/23

**嚴重性**: 🟡 中等

**類型**: CLI

---

### [BUG-003] 重啟後命令事件失效

**問題**: 調用 `sdk.restart()` 後，通過 `@command` 註冊的命令無法被觸發，表現為發送命令後機器人無響應。

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

**問題**: `Event.is_friend_add()` 檢查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 檢查 `detail_type == "friend_delete"`，但 OneBot12 標準定義的 `detail_type` 值為 `"friend_increase"` 和 `"friend_decrease"`。與 `notice.py` 中 `on_friend_add`/`on_friend_remove` 裝飾器使用的值不一致，導致通過裝飾器註冊的處理器觸發時，對應的 `is_friend_add()`/`is_friend_delete()` 判斷方法返回 `False`。

**原因**: `wrapper.py` 中使用了非標準的命名，而 `notice.py` 使用了正確的 OB12 標準命名。

**影響版本**: 實裝至今

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `is_friend_add()` 的匹配值從 `"friend_add"` 改為 `"friend_increase"`，`is_friend_delete()` 從 `"friend_delete"` 改為 `"friend_decrease"`。

**修復日期**: 2026/04/13

**嚴重性**: 🟡 中等

**類型**: 事件系統

---

### [BUG-006] adapter.clear() 未清理 _started_instances 導致重啟後狀態不正確

**問題**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、處理器和 `_bots`，但遺漏了 `_started_instances` 集合。如果適配器正在運行時調用 `clear()`，`_started_instances` 會保留懸空引用，導致重啟後狀態判斷錯誤。

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

**原因**: 開發時使用了舊版 API，後續新增的 `wait_for()` 使用了正確的 API 但未回溯修復舊代碼。

**影響版本**: 2.3.0-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `command.py` 中兩處 `asyncio.get_event_loop()` 替換為 `asyncio.get_running_loop()`。

**修復日期**: 2026/04/13

**嚴重性**: 🟢 輕微

**類型**: 事件系統

---

### [BUG-008] Bot 離線事件在 shutdown 過程中被重複提交

**問題**: 調用 `adapter.shutdown()` 關閉所有適配器時，`_update_bot_status()` 會在關閉流程中反覆提交 Bot 離線事件，導致同一批 Bot 被多次標記離線並觸發多次 `adapter.bot.offline` 生命週期事件。

**原因**: 2.4.0-dev.1 引入的 Bot 狀態追蹤系統未在 `shutdown()` 期間設置"正在關閉"標誌，`_update_bot_status()` 無法區分正常離線與關閉流程中的級聯離線。

**影響版本**: 2.4.0-dev.1 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.1

**修復內容**: 在 `AdapterManager` 中新增 `_is_being_shutdown` 標誌，`shutdown()` 開始時置為 True、結束時清除；`_update_bot_status()` 檢查該標誌後跳過關閉過程中的重複提交。

**修復日期**: 2026/04/21

**嚴重性**: 🟡 中等

**類型**: 適配器

---

### [BUG-009] LazyModule 同步訪問 BaseModule 導致未初始化完成

**問題**: 用戶在同步上下文中訪問懶加載的 BaseModule 屬性時，模塊使用 `loop.create_task()` 異步初始化但不等待，導致屬性訪問時可能未初始化完成，引發競態條件。

**原因**: `_ensure_initialized()` 對 BaseModule 使用 `loop.create_task(self._initialize())` 後立即返回，未確保初始化完成。

**影響版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**: 在同步上下文中，BaseModule 的初始化改為使用 `asyncio.run(self._initialize())`，確保初始化完成後再返回。保持透明代理特性，用戶無需感知同步/異步差異。

**修復日期**: 2026/04/21

**嚴重性**: 🟡 中等

**類型**: 加載系統

---

### [BUG-010] 配置系統多線程寫入導致數據丟失

**問題**: 在多線程環境下，多個線程同時調用 `config.setConfig()` 時，`_flush_config()` 讀取-修改-寫入操作不是原子性的，可能导致部分寫入丟失。

**原因**: `_flush_config()` 雖然使用了 `RLock`，但文件讀取和寫入之間沒有文件鎖保護，且 `_schedule_write` 的 Timer 可能被多次觸發導致覆蓋。

**影響版本**: 2.3.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**:
1. 添加文件鎖機制（`_file_lock`）確保文件操作原子性
2. 使用臨時文件寫入後原子性重命名（`os.replace`/`os.rename`）
3. 改進 `_schedule_write` 的 Timer 取消和重新調度邏輯

**修復日期**: 2026/04/21

**嚴重性**: 🔴 嚴重

**類型**: 配置系統

---

### [BUG-011] Windows 下 CTRL+C 無法停止程序

**問題**: 在 Windows 上直接運行 `python main.py` 時，按下 CTRL+C 無法終止程序。程序正常啟動並輸出路由伺服器資訊後，CTRL+C 完全無響應，只能通過任務管理器強殺進程。而通過 `epsdk run` 啟動時可以正常停止——但 `epsdk run` 是通過子進程模型運行的。

**原因**: Hypercorn ASGI 伺服器的 `serve()` 函數內部通過 `signal.signal(SIGINT, handler)` 注冊了自己的 SIGINT 處理器，覆蓋了 Python 預設的 `KeyboardInterrupt` 處理機制。當通過 `asyncio.create_task()` 啟動 Hypercorn 作為後台任務時，Hypercorn 的內部 shutdown 流程無法正常觸發（因為它期望的是 `worker_serve` 模式），導致 CTRL+C 信號被 Hypercorn 吞掉但不會引發任何清理動作。

**影響版本**: 2.3.6 - 2.4.2

**修復版本**: 2.4.3-dev.0

**修復內容**:
1. 將 ASGI 伺服器從 Hypercorn 切換為 Uvicorn（`pyproject.toml` 依賴變更）
2. 使用 `uvicorn.Server._serve()` 直接啟動伺服器，**繞過** `capture_signals()` 信號處理上下文管理器
3. 通過 `server.should_exit = True` 實現優雅停止，超時則取消後台任務
4. 同步移除子進程運行模型和 `runtime/cleanup.py` 清理模塊（子進程清理機制不再需要）

**修復日期**: 2026/04/28

**嚴重性**: 🔴 嚴重

**類型**: CLI / 運行時

---

### [BUG-012] 熱重啟後已更新模塊的 Python 代碼未生效

**問題**: 執行 `sdk.restart()` 軟重啟後，已通過 `epsdk install` 升級的模塊/適配器的新代碼（如新增 API 路由）不生效，仍運行舊版本邏輯。必須完全重啟進程才能加載最新代碼。

**原因**: `_do_restart()` 在重新初始化時調用 `entry_point.load()`，但該函數從 `sys.modules` 返回了緩存的舊版本模塊對象，而非從磁盤重新加載。

**影響版本**: 早期版本 - 2.4.3-dev.1

**修復版本**: 2.4.3-dev.1

**修復內容**: 在 `uninit()` 後、`init()` 前清理 `sys.modules` 中已加載模塊/適配器包的緩存，使 `entry_point.load()` 從磁盤加載最新代碼。新增 `_collect_top_level_modules()` 與 `_invalidate_module_cache()` 輔助方法，通過 `top_level.txt` 或 entry-point value 推導頂層模塊名。

**修復日期**: 2026/05/03

**嚴重性**: 🔴 嚴重

**類型**: 加載系統 / 運行時

---

### [BUG-013] 模塊加載策略排序邏輯錯誤

**問題**: `ModuleLoadStrategy` 提供了 `priority` 字段用於聲明模塊的初始化優先級，但加載策略的實現存在失誤，導致模塊未按預期的優先級順序初始化，實際按 `entry_points()` 的預設順序加載。當模塊間存在加載依賴時，無法通過 `priority` 確保正確的初始化先後關係。

**原因**: 加載策略的實現中排序邏輯有誤，`initialize_modules()` 未使用 `priority` 對模塊列表進行排序。

**影響版本**: 2.3.4 - 2.4.5-dev.2

**修復版本**: 2.4.5-dev.3

**修復內容**: 在 `initialize_modules()` 遍歷前，按 `priority` 降序排序模塊列表。同 priority 的模塊保持原有相對順序（穩定排序）。

**修復日期**: 2026/05/15

**嚴重性**: 🟡 中等

**類型**: 加載系統

---

### [BUG-014] 適配器中間件返回 None 導致事件數據丟失

**問題**: `adapter.emit()` 在執行 OneBot12 中間件鏈時，如果某個中間件返回 `None`（例如忘記 `return data`），後續中間件和所有事件處理器收到的 `processed_data` 變為 `None`，導致事件處理完全失效。

**原因**: 中間件鏈的實現 `processed_data = await middleware(processed_data)` 未檢查返回值是否為 `None`，直接覆蓋了上一步的處理結果。

**影響版本**: unknown - 2.4.5-dev.3

**修復版本**: 2.4.5-dev.4

**修復內容**: 中間件返回 `None` 時忽略該返回值，保留原數據繼續傳遞，並輸出 warning 級別日誌。

**修復日期**: 2026/05/15

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 事件系統

---

### [BUG-015] 配置文件路徑依賴工作目錄

**問題**: `ConfigManager` 的配置文件路徑預設為相對路徑 `"config/config.toml"`，在運行時依賴 `os.getcwd()` 解析。如果工作目錄在運行期間發生變化（例如通過 `os.chdir()`），配置文件的讀寫操作會指向錯誤的位置，導致配置丟失或讀取到舊數據。

**原因**: `__init__` 中直接存儲相對路徑，未在初始化時將其解析為絕對路徑。

**影響版本**: 2.3.7 - 2.4.5-dev.3

**修復版本**: 2.4.5-dev.4

**修復內容**: 在 `ConfigManager.__init__()` 中，如果傳入的路徑為相對路徑，自動通過 `os.path.abspath()` 解析為絕對路徑。

**修復日期**: 2026/05/15

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-016] BaseStorage 將存儲值 None 與鍵不存在混淆

**問題**: `BaseStorage.get_multi()` / `__getattr__()` 無法區分"鍵不存在"與"鍵的值就是 `None`"兩種情況，用戶顯式存入 `None` 後再讀取時會被當作鍵不存在處理。

**原因**: 取值邏輯直接用 `value is None` 判斷鍵是否存在，缺少獨立的"缺失"標記。

**影響版本**: 早期版本 - 2.4.6-dev.6

**修復版本**: 2.4.6-dev.6

**修復內容**: 引入 `_SENTINEL` 哨兵值區分"鍵不存在"與"值為 None"，二者不再混淆。

**修復日期**: 2026/06/07

**嚴重性**: 🟡 中等

**類型**: 存儲

---

### [BUG-017] WebSocket 路由 auto_accept 標誌在服務重啟後丟失

**問題**: 服務重啟（如 `sdk.restart()`）後，所有 WebSocket 路由的 `auto_accept` 配置都變回 `False`，原本期望自動 accept 的連接變為掛起狀態，客戶端長時間收不到響應，表現為 WS 連接卡死。

**原因**: `_restore_routes_from_records()` 在從持久化記錄恢復路由時把 `auto_accept` 硬編碼為 `False`，未讀取原始記錄中的值；同時路由存儲元組也從二元組擴展為三元組時未同步更新恢復邏輯。

**影響版本**: 2.3.8-dev.0 - 2.4.6-dev.6

**修復版本**: 2.4.6-dev.6

**修復內容**: 路由存儲元組擴展為 `(handler, auth_handler, auto_accept)`，`_restore_routes_from_records()` 從記錄讀取真實 `auto_accept` 值而非硬編碼 `False`。

**修復日期**: 2026/06/07

**嚴重性**: 🔴 嚴重

**類型**: 路由

---

### [BUG-018] HTTP/WS 客戶端並發調用導致崩潰與連接洩漏

**問題**: `Core/client.py` 的 HTTP 與 WebSocket 客戶端在並發場景下存在多個穩定性缺陷，會導致連接洩漏或進程崩潰：
- 多協程並發調用 `ClientWebSocket.receive()` 時 aiohttp 抛出 `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` 並發調用可能創建多個 session 且 `_drain_sessions()` 未關閉舊連接，造成連接洩漏
- `request()` 的異常捕獲順序錯誤：`except ClientConnectionError`（ErisPulse 異常）永不觸發，aiohttp 的連接錯誤被通用 `except Exception` 接住，導致"連接重試 + session 重建"邏輯（死代碼）從未執行
- `send_json()` 忽略 `mode="binary"` 參數；`_get_ws_session()` 未傳入默認請求頭

**原因**: 客戶端初次實現（2.4.6-dev.5）缺少並發保護與異常分類，對 aiohttp 異常體系與 ErisPulse 自定義異常的繼承關係處理不當。

**影響版本**: 2.4.6-dev.5 - 2.4.8

**修復版本**: 2.4.8

**修復內容**:
1. 新增 `_recv_lock` 序列化所有 `receive()` / `receive_text()` / `receive_bytes()` 調用
2. 新增 `_session_lock` 保護 session 創建；`_drain_sessions()` 改為異步方法並真正關閉舊 session
3. 重構 `request()` 異常捕獲順序：`asyncio.TimeoutError` → `aiohttp.ClientConnectionError`（觸發 session 重建）→ `aiohttp.ClientError` → `ClientError`（透傳）→ `Exception`
4. 修復 `send_json()` 的 mode 處理、`_get_ws_session()` 默認請求頭透傳、`close()` 的並發競態、`HttpResponse.__aexit__` 重複 `release()`

**修復日期**: 2026/06/12

**嚴重性**: 🔴 嚴重

**類型**: 客戶端

---

### [BUG-019] 適配器熱重載時路由衝突導致重載失敗

**問題**: 第三方模塊（如 Dashboard）觸發適配器熱重載，或適配器啟動失敗重試時，因上次註冊的舊路由（如 `onebot11_default`）未清理，拋出 `WebSocket路徑 ... 已註冊` 衝突，導致重載失敗。需要完全重啟進程才能恢復。

**原因**: `AdapterManager.shutdown()` 僅以 `unregister_all_by_namespace(platform)` 清理路由，但適配器（如 OneBot11）以 `onebot11_{account_name}` 為命名空間註冊 WS 路由，顆粒度不匹配導致清理為空操作；啟動失敗重試路徑也未清理上次殘留路由。

**影響版本**: 早期版本 - 2.4.9

**修復版本**: 2.4.9

**修復內容**:
1. 路由註冊時通過 `current_owner` ContextVar 自動追蹤 `owner → namespace` 歸屬關係
2. 新增 `unregister_all_by_owner(owner)`，停止/重啟時同時按 owner 清理，覆蓋細顆粒度命名空間
3. 新增 `_stop_adapter(platform)` 原語（"停止即清理"），將停止適配器與回收其註冊的資源綁定在一次調用裡，`restart()` 和啟動失敗重試均經此入口
4. 新增框架級 `adapter.restart(platform)` API，第三方模塊應調用此方法而非直接操作適配器實例

**修復日期**: 2026/06/12

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 路由

---

### [BUG-020] 子進程模式 `ep run <script>` 找不到腳本所在目錄的子包

**問題**: 使用 `ep r .\main.py` 非熱重載模式運行腳本時，如果腳本有相對導入（如 `from qg import ...`），會報 `No module named 'qg'` 錯誤。而 `--reload` 模式可以正常運行。

**原因**: 非熱重載模式直接調用 `runpy.run_path()` 執行腳本，該函數不會自動將腳本所在目錄加入 `sys.path`。而 `--reload` 模式通過 `subprocess.Popen` 子進程運行，子進程自動繼承當前工作目錄，`sys.path[0]` 即為腳本所在目錄，所以能正常工作。

**影響版本**: 2.5.0 - 2.5.2-dev.0

**修復版本**: 2.5.2-dev.0

**修復內容**: 在 `runpy.run_path()` 調用前，手動將腳本所在目錄插入 `sys.path[0]`。

**修復日期**: 2026/06/27

**嚴重性**: 🟡 中等

**類型**: CLI

---

### [BUG-021] SQL 查詢建構器拒絕合法通配符和列表達式

**問題**: `SQLiteQueryBuilder` 的 `_build_select_sql()` 對所有 SELECT 列調用 `_validate_identifier()`，該函數使用嚴格的白名單正則 `^[a-zA-Z_][a-zA-Z0-9_]*$`，導致合法 SQL 語法被誤判為不安全列名：

- `SELECT *` — `*` 是 SQL 標準通配符
- `SELECT COUNT(*)` — 聚合函數
- `SELECT users.name` — 限定列名
- `SELECT col AS alias` — 列別名

其中 `Select("*")` 被 Cron 等模塊使用，導致模塊 `on_load` 執行失敗，模塊無法加載。

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

### [BUG-022] _resolve_account() 賬戶解析迴歸（_accounts_data 未填充）

**問題**: 2.5.2 配置系統重構後，聲明了 `AccountConfigClass` 的多賬戶適配器在調用 `wait_reply`、`reply` 等需要發送消息的方法時，報錯 `ValueError("未聲明 AccountConfigClass，無法解析賬戶")`。即使適配器正確配置了多賬戶資訊，賬戶解析仍然失敗。

**原因**: 2.5.2-dev.5 將 `_load_accounts()`（負責讀取配置 + 校驗 + 填充 `_accounts_data`）重構為 `_ensure_accounts_exist()`（僅生成配置模板），但 `_resolve_account()` 仍檢查 `self._accounts_data is None`。由於 `_ensure_accounts_exist()` 不再填充 `_accounts_data`，該屬性始終為 `None`，導致 `_resolve_account()` 提前返回 `(None, None)`，賬戶解析完全失效。

**根因鏈路**:
```
_load_accounts() 被刪除
  → __init__ 不再填充 _accounts_data
    → _accounts_data 恆為 None
      → _resolve_account() 檢查 _accounts_data is None → return (None, None)
        → 下游調用 _resolve_account 的地方（如 call_api）拿到 None
          → 觸發報錯
```

**影響版本**: 2.5.2-dev.5 - 2.5.2

**修復版本**: 2.5.3

**修復內容**: 在 `BaseAdapter.__init__` 中，`_ensure_accounts_exist()` 之後恢復 `_accounts_data` 的填充：
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # 恢復填充，數據源為實時讀取的 accounts 屬性
```
`_resolve_account()` 逻辑保持不变，完全向后兼容：
- 不聲明 `AccountConfigClass` 的适配器：`_accounts_data` 保持 `None` → 返回 `(None, None)`
- 声明了 `AccountConfigClass` 的适配器：`_accounts_data` 被填充 → 正常解析
- 覆写 `_load_accounts` 或手动设置 `_accounts_data` 的适配器：在 `super().__init__()` 后覆盖，优先级最高

**修復日期**: 2026/07/07

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 配置系統

---

### [BUG-023] 修改賬戶配置後適配器緩存未刷新導致賬戶解析失敗

**問題**: 用戶通過 Dashboard 修改多賬戶適配器的賬戶配置（如填寫 token）後，適配器仍使用舊緩存，調用發送消息相關方法時報 `未找到可用賬戶 (account_id=default)`。必須重啟進程才能讓新配置生效。

**原因**: `_accounts_data` 僅在 `BaseAdapter.__init__` 時從配置存儲讀取一次，之後不再刷新。`AdapterManager._run_adapter()` 與 `restart()` 在調用 `adapter.start()` 前未重新讀取賬戶配置，導致緩存與實際配置脫節。

**影響版本**: 2.4.6 - 2.5.4

**修復版本**: 2.5.4

**修復內容**: 在 `AdapterManager._run_adapter()` 和 `restart()` 中，調用 `adapter.start()` 之前刷新 `adapter._accounts_data = adapter.accounts`，確保每次啟動時使用最新配置。

**修復日期**: 2026/07/09

**嚴重性**: 🔴 嚴重

**類型**: 適配器 / 配置系統

---

### [BUG-024] storage.set() 寫入大數字 ID 鍵時觸發 OOM Kill

**問題**: 調用 `storage.set()` 寫入包含大純數字段（如 QQ 群號 `871684833`）的嵌套鍵路徑時，進程被容器 OOM Kill（退出碼 -9），服務直接崩潰無法恢復。

**原因**: `_set_nested_value` 的遞歸實現中，嵌套鍵路徑裡的純數字段被 `isdigit()` 误判為列表索引，觸發 `current.extend([None] * (index - len(current) + 1))`，試圖分配數億元素的列表，瞬間耗盡內存。

**根因鏈路**:
```
鍵路徑包含純數字段（如群號 871684833）
  → isdigit() 误判為數組索引
    → extend([None] * (871684833 - len(current) + 1))
      → 試圖分配數億元素
        → 內存耗盡 → 容器 OOM Kill（退出碼 -9）
```

**影響版本**: 2.5.1 - 2.5.5

**修復版本**: 2.5.5

**修復內容**:
1. 預創建中間層時始終使用字典，不再根據下一段是否為數字猜測容器類型
2. 設置最終值時，僅當容器本身已是列表且索引小於 `STORAGE_MAX_LIST_INDEX`（10000）時才按索引處理，超大索引安全跳過
3. 將遞歸實現改為迭代實現，消除原代碼中潛在的無限遞歸風險
4. 新增 `STORAGE_MAX_LIST_INDEX` 常量到 `Core/constants.py`，集中管理索引安全上限

**修復日期**: 2026/07/10

**復現步驟**:
```python
# 寫入包含大數字段（如 QQ 群號）的嵌套鍵路徑即可觸發
await sdk.storage.aset("groups.871684833.name", "某群")
# → 進程內存瞬間飆升，被 OOM Kill
```

**回歸測試**: `tests/unit/test_unit_storage.py` 新增 4 個回歸用例
- `test_nested_key_numeric_segment_as_dict_key` — 精確復現 OOM 場景
- `test_nested_key_numeric_segment_multiple` — 多個連續數字段均作為字典鍵
- `test_nested_key_existing_list_index_set_within_limit` — 已有列表合理索引寫入
- `test_nested_key_list_index_safety_limit` — 超大索引安全限制驗證

**嚴重性**: 🔴 嚴重

**類型**: 存儲

---

### [BUG-025] on_config_update 回調未被核心路由

**問題**: `on_config_update(old, new)` 回調在基類（`BaseModule` / `BaseAdapter`）中已定義，但框架核心未將其與配置變更事件關聯。實際表現：通過配置管理面板改配置時可以觸發，而手動編輯 `config.toml` 或代碼調用 `setConfig()` 時不會觸發 `on_config_update`。

**原因**: `ConfigManager` 在配置變更時會發射 `config.set` / `config.updated` 生命週期事件，但缺少將這些事件轉發到各組件 `on_config_update` 方法的訂閱邏輯。

**根因鏈路**:
```
核心未訂閱 config.set / config.updated
  → 配置變更事件無轉發
    → on_config_update 未被調用
      → 手動編輯文件 / 代碼 setConfig 不觸發熱更新回調
```

**影響版本**: 全版本

**修復版本**: 2.6.2

**修復內容**: `ModuleManager` / `AdapterManager` 註冊 `config.set`（覆蓋代碼 `setConfig()` 路徑）與 `config.updated`（覆蓋手動編輯文件路徑）事件訂閱，按配置鍵前綴匹配後調用對應組件的 `on_config_update`，傳入類型安全的配置對象。同時修復 `_flush_config()` 寫入文件後未同步 `_config_mtime` 的問題，避免框架自身寫入被文件監聽任務誤判為外部修改而重複觸發 `config.updated`。

**兼容性說明**: 配置熱更新現由框架核心統一維護。此前由配置管理面板代為觸發的邏輯已移除，升級框架後需同步升級配置管理面板，否則會出現重複觸發（核心 + 面板各調一次）。`on_config_update` 方法簽名與語義保持不變，子類無需修改。

**修復日期**: 2026/07/23

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-026] notice/request 事件 reply 目標推斷錯誤

**問題**: 在群通知事件（如成員加群 `group_member_increase`）中調用 `event.reply()`，消息被發送到觸發事件的用戶私聊，而非事件所在的群。好友通知事件同理，回覆目標可能錯亂。

**原因**: `infer_receive_type()` 將事件的 `detail_type` 直接當作會話類型返回。對於 message 事件這是正確的（`detail_type` 值 `private`/`group` 即會話類型），但 notice/request 事件的 `detail_type` 是語義子類型（如 `group_member_increase`、`friend_increase`），不是會話類型。後續的 `convert_to_send_type()` 和 `get_id_field()` 在映射表中找不到該值，回退到預設的 `"user"` / `"user_id"`，導致回覆目標錯亂。

**根因鏈路**:
```
notice 事件 detail_type="group_member_increase"
  → infer_receive_type() 直接返回 "group_member_increase"
    → convert_to_send_type("group_member_increase") 不在映射表 → 回退 "user"
    → get_id_field("group_member_increase") 不在映射表 → 回退 "user_id"
      → target_id = event["user_id"]  ← 新成員私聊（而非群）
```

**影響版本**: 全版本

**修復版本**: 2.7.0-dev.3

**修復內容**: `infer_receive_type()` 增加判斷——`detail_type` 只有在是已知會話類型（標準類型或自定義類型）時才直接返回；否則根據 ID 字段（`group_id` / `channel_id` / `user_id` 等）推斷正確的會話類型。

**回歸測試**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference`（10 用例）

**修復日期**: 2026/07/29

**嚴重性**: 🟢 輕微

**類型**: 事件系統

---

### [BUG-027] 路由限流清理任務使用固定窗口導致長窗口限流規則失效

**問題**: 將路由限流配置為長窗口規則（如 `100/hour`、`{"requests": 100, "window": 3600}`）時，限流形同虛設——實際表現近似 `100/minute`（每小時可放過至約 6000 次請求），完全無法起到預期的小時級防護作用。

**原因**: `_apply_rate_limit` 解析得到每路由的實際 `window`（最高 3600 秒），per-request 檢查也確實使用該窗口；但後台清理任務 `_cleanup_expired_rate_limits` 卻用固定常量 `DEFAULT_RATE_LIMIT_WINDOW_SECS`（60 秒）作為所有路由的統一清理閾值。於是 `100/hour` 路由中早於 60 秒的時間戳被清理任務提前清除，小時窗口內永遠累積不到接近 100 條記錄，限流被嚴重削弱。

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

**問題**: 用戶手動編輯 `config.toml` 保存到一半（產生瞬時的語法錯誤）時，配置監聽後台線程會檢測到 mtime 變化、重載配置，但加載失敗後仍以空配置 `{}` 發射 `config.updated` 事件，導致適配器/模塊的 `on_config_update` 收到空配置、誤以為所有配置項被清空而回退預設值。此外監聽循環用 `except Exception: pass` 靜默吞掉所有異常，watcher 故障無從排查。

**原因**: 兩個缺陷疊加：
1. `_load_config` 在 TOML 語法錯誤/權限錯誤時把 `self._cache` 擦寫為 `{}`，但後台監聽線程 `_watch_loop` 與緩存超時路徑 `_check_cache_validity` 都在調用 `_load_config()` 後**無條件**執行 `_emit_config_updated()`，把"加載失敗產生的空緩存"當作真實變更廣播。
2. `_watch_loop` 的 `except Exception` 改為以 warning 級別記錄（新增 i18n 鍵 `core.config.watcher_error`，五語言同步）

**根因鏈路**:
```
用戶保存到一半 → TOML 語法錯誤
  → _load_config() 擦寫 _cache = {}
    → _watch_loop 無條件 _emit_config_updated(new_config={})
      → 适配器/模塊 on_config_update 收到空配置
        → 误判配置被清空，回退預設值
```

**影響版本**: 2.6.2-dev.1 - 2.7.0-dev.4

**修復版本**: 2.7.0-dev.5

**修復內容**:
1. `_load_config` 改為返回 `bool`；TOML 語法錯誤/權限/其他錯誤時**保留上次有效緩存**（不再擦寫為 `{}`），僅記錄診斷日誌並返回 `False`
2. `_watch_loop` 與 `_check_cache_validity` 僅在 `_load_config()` 返回 `True` 時才發射 `config.updated`
3. `_watch_loop` 的 `except Exception` 改為以 warning 級別記錄（新增 i18n 鍵 `core.config.watcher_error`，五語言同步）

**修復日期**: 2026/07/31

**回歸測試**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`、`test_permission_denied_logs_clear_message`（更新為驗證保留緩存 + 返回 False）

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-030] 配置 watcher 競態導致 setConfig 延遲寫入靜默丟數據

**問題**: 多個用戶報告使用 `config.setConfig(key, value)`（預設 `immediate=False`）後，自己的模塊配置未寫入 `config.toml`，而其它模塊的配置正常。設置 `immediate=True`（強制刷盤）可避開。表現為：運行期寫入的配置在下次重啟後丟失，啟動期模板生成的配置保留。

**原因**: 兩個疊加缺陷：
1. **邏輯缺陷**：`_watch_loop` 在 `_check_file_change()` 返回 `True` 時無條件 `_dirty_keys.clear()` 丟棄所有待寫鍵。但 `_check_file_change()` 僅用 `!=` 對比 mtime，框架自身的 `_flush_config` 寫盤也會改變 mtime——雖然 `_flush_config` 在寫盤後更新 `_config_mtime`，但 watcher 線程在文件寫入與 mtime 賦值之間（以及粗粒度文件系統上）仍可能觀測到 mtime 差值，誤判為"外部修改"並清空全部待寫鍵。
2. **線程缺陷**：`_watch_loop` 操作 `_write_timer`/`_dirty_keys` 時未持有 `_lock`，與 `setConfig`（持鎖寫 `_dirty_keys`）、`_schedule_write`（持鎖寫 `_write_timer`）存在數據競爭。

**根因鏈路**:
```
模塊A setConfig(immediate=True) → flush 寫盤，mtime 變化
  → 用戶模塊 setConfig(immediate=False) → 進入 _dirty_keys，5s 後刷盤
    → watcher 輪詢，_check_file_change 觀測到先前自身寫入的 mtime 差值
      → _dirty_keys.clear() → 用戶模塊的待寫鍵被靜默丟棄
        → 重啟後配置缺失
```

**影響版本**: 2.6.0 - 2.7.0

**修復版本**: 2.7.1

**修復內容**:
1. 新增 `_last_self_write_mtime` 字段，`_flush_config` 寫盤後同步記錄；`_check_file_change` 在 mtime 變化時先對比該值，匹配則判定為自身寫入返回 `False`
2. `_watch_loop` 整段持 `_lock`；真正外部修改時保留 `_dirty_keys`（merge 語義），下次 flush 與外部內容合併（臟鍵優先），不再 `clear()`
3. `getConfig`/`_check_cache_validity` 路徑不受影響（其 reload 本就不清臟鍵）

**修復日期**: 2026/08/06

**回歸測試**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`、`test_external_change_preserves_dirty_keys`、`test_flush_merges_dirty_with_external`

**嚴重性**: 🔴 嚴重

**類型**: 配置系統

---

### [BUG-032] 配置延遲刷盤期間「寫後立讀」讀到舊值

**問題**: `config.setConfig()`（預設 `immediate=False` 延遲約 5 秒刷盤）寫入點分鍵後，立即讀取其**父級/祖先節點**（如 `set_erispulse_section("scope.actions.MyModule", {...})` 後調用 `get_erispulse_config()`）返回的是舊值，寫入的子鍵"消失"，直到刷盤後才可見。作用域配置熱更新等"寫-讀-寫"場景受影響（2.8.0 測試插件 `/t_section` 用例暴露）。

**原因**: `setConfig` 將點分鍵以**扁平形式**存入待寫隊列 `_dirty_keys`，僅 `getConfig` 的**精確鍵查詢**命中待寫隊列；樹形路徑查詢（`getConfig("ErisPulse.scope")`）只走緩存樹，不疊加待寫值——延遲刷盤（`_flush_config` 才將臟鍵合併進緩存並清隊列）期間形成讀-你-寫斷層。

**影響版本**: 2.6.0 - 2.8.0-dev.1

**修復版本**: 2.8.0-dev.1

**修復內容**: `getConfig` 引入待寫疊加語義——① 精確命中待寫鍵直接返回（原有行為不變）；② 待寫鍵是查詢鍵的祖先 → 取最長待寫祖先，在其值子樹內解析剩餘路徑；③ 待寫鍵是查詢鍵的後代 → 構建疊加子樹（`_dirty_overlay`）與緩存子樹深合併（`_deep_merge`，override 优先，不修改原緩存對象）。無待寫鍵時走原快路徑，零額外開銷。

**修復日期**: 2026/09/04

**回歸測試**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`、`test_get_config_overlay_merges_with_cache_siblings`、`test_get_config_overlay_new_branch`、`test_get_config_dirty_ancestor_query`、`test_get_config_dirty_exact_key_still_wins`

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-033] wait_reply 挂起的回覆被高優先級處理器餓死

**問題**: 模塊調用 `wait_reply()` 等待用戶回覆期間，若該回覆消息被更高優先級的事件處理器認領（`mark_processed()`），命令分發器在入口看到 `_processed` 標記後直接返回，排在分發器末尾的回覆匹配邏輯永遠執行不到——等待方收不到回覆，只能乾等到超時返回 `None`。典型觸發場景：使用了高優先級消息處理器（記錄/審計/拦截類）的機器人，所有對話式交互隨機性失效。

**原因**: 回覆匹配 `_check_pending_reply` 掛在 `_handle_message` 末尾（命令未匹配時才執行），而 `_processed` 檢查在其之前——認領檢查與回覆命中判定的順序顛倒。交互等待是框架級的會話延續機制而非競爭處理器，不應受其他處理器的認領影響。

**影響版本**: 2.2.0-dev.0 - 2.8.0-dev.1

**修復版本**: 2.8.0-dev.2

**修復內容**: 回覆命中判定提前至 `_handle_message` 入口（`_processed` 檢查之前、僅 message 事件）：先嘗試完成掛起的對話，命中後事件被標記已處理、下方檢查自然短路；未命中則繼續原有命令匹配流程。同時判定鏈委託新的交互會話管理器（`Core/Event/interaction.py`），順帶獲得按歸屬取消與權限复查能力。

**修復日期**: 2026/09/08

**回歸測試**: `tests/unit/test_unit_interaction.py`（`TestRegisterResolve` 命中/未命中/認領標記）、`tests/unit/test_unit_event.py`（wait_reply 全鏈路）

**嚴重性**: 🟡 中等

**類型**: 事件系統 / 命令系統

---

### [BUG-034] scope.set_module(..., persist=False) 運行時綁定被任意後續配置寫入靜默沖掉

**問題**: `scope.set(path, value, persist=False)` 寫入的運行時綁定（文檔承諾不落盤、進程重啟即失效、模塊卸載時清理）會隨任意一次無關的 `persist=True` 寫入（預設值，如模塊 `set_module` / WebUI 保存配置）被差量寫入用戶 `config.toml`；此後即使模塊卸載註銷了運行時綁定，下次配置重載時該綁定仍從磁盤"復活"繼續生效、進程重啟後依然存在——與"運行時綁定不落盤"的語義契約相反，且極難排查。

**原因**: 根因鏈路：`ScopeManager.set()` 先把值寫入內存配置樹 `_data`（運行時綁定同樣直接寫入 `_data`）→ 持久化分支對**整棵 `_data`** 做深拷貝快照提交給 `update_erispulse_config` 差量落盤 → 快照中混入了 `persist=False` 綁定的值。`delete(persist=True)` 同源：把 `_data` 的活引用（`parent` 節點）交給延遲寫臟隊列，延遲刷盤期間對該節點下兄弟鍵的運行時修改會被一並落盤，且活引用在臟隊列滯留期間存在跨寫污染窗口。

**影響版本**: 2.8.0-dev.2 - 2.9.0-dev.0

**修復版本**: 2.9.0-dev.2

**修復內容**: 引入持久化基線 `_persisted_tree`（配置樹重建時以磁盤加載、校驗後的樹刷新）作為磁盤真相鏡像：`set(persist=True)` 只在基線上應用本次變更後提交差量，運行時綁定永不進入持久化內容；"寫後立讀"改用內存最終態快照直接恢復，不再經 `_apply_tree` 重建以免污染基線。`delete(persist=True)` 同口徑：在基線上應用刪除並把基線子樹的深拷貝交給持久化層；`set_action` 整體替換語義先按同口徑刪除再寫入，舊規則鍵不殘留在持久化內容中。

**修復日期**: 2026/09/27

**復現步驟**: ① 模塊內執行 `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`；② 觸發任意持久化寫入（如另一模塊調用 `set_module`）；③ 打開 `config/config.toml`，可見 `debug_mode` 已被寫入（修復前）；④ 卸載該模塊（運行時綁定被註銷）後觸發配置重載，`scope.get("bots.p.debug_mode")` 仍返回綁定值。

**回歸測試**: `tests/unit/test_unit_scope.py::TestPersistBaseline`（運行時綁定不隨無關持久化寫入落盤 / 卸載註銷後配置重載不復活 / delete 提交基線子樹不帶運行時兄弟鍵 / set_action 替換不留殘留鍵 / cache_size 配置生效）

**嚴重性**: 🔴 嚴重

**類型**: 配置系統

---

### [BUG-035] 整節寫與點分寫並存時讀寫不一致（點分覆寫丟失）

**問題**: 延遲刷盤窗口內，同節並存整節寫（`setConfig("Mod", {...})`，如 `BaseModule.cfg` 寫回）與點分寫（`setConfig("Mod.key", v)`，如配置熱更 / 測試工具覆寫）時有兩個變體：變體 A（讀路徑）——`getConfig("Mod")` 整節讀取返回舊整節待寫快照，看不到更晚的點分覆寫（點分讀取路徑正常）；變體 B（寫路徑，更重）——點分寫在前、整節寫在後（測試工具注入覆寫 → 模塊 `self.cfg = ...` 寫回的常見時序）時，flush 按插入序應用臟鍵，整節寫整體替換該節，**點分覆寫在磁盤上永久丟失**。生產環境"配置熱更 + 模塊運行時寫回"組合即可觸發，與測試環境無關（ErisPulse-DailyCard 測試反饋暴露）。

**原因**: `getConfig` 第①段（精確命中 `_dirty_keys`）提前 `return self._dirty_keys[key]`，完全繞過第④段 `_dirty_overlay` 後代疊加；`_flush_config` 按 `_dirty_keys` 插入序應用臟鍵，整節寫恰好排在點分寫之後時點分值被整體替換。另：第①段返回臟隊列**原對象引用**，調用方原地修改返回 dict 會直接改變待落盤狀態。

**影響版本**: 2.6.0 - 2.9.0-dev.2

**修復版本**: 2.9.0-dev.2

**修復內容**: 脏窗口內統一為**特異性优先**語義——點分（更具體）待寫值優先於整節（較寬）待寫值，讀路徑與落盤路徑同口徑：① `getConfig` 精確命中待寫鍵後仍疊加 `_dirty_overlay` 後代待寫值（非 dict 值返回疊加子樹，與③+④標量邊角同口徑）；② `_flush_config` 脏鍵按路徑深度排序應用（整節/祖先先、點分/後代後，穩定排序保持同深度寫入時序）。代價：同一臟窗口內（約 5 秒）整節寫回無法覆蓋仍掛起的點分寫——讀路徑修復後讀-改-寫自然攜帶點分值，實際影響面極小。③ 涉及待寫值的 `getConfig` 返回（精確命中 / 祖先子樹 / 疊加合併）改為 `copy.deepcopy` 隔離拷貝，不再泄漏臟隊列內部引用；無臟鍵快路徑與純緩存讀行為不變。

**修復日期**: 2026/09/28

**復現步驟**: ① `setConfig("FB.y", 1)`；② `setConfig("FB", {"z": 2})`；③ `force_save()`——修復前磁盤只剩 `[FB] z = 2`（y 丟失），修復後 `{"y": 1, "z": 2}`；變體 A：步驟①②後不落盤直接 `getConfig("FB")`——修復前不含 `y`，修復後可見。

**回歸測試**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency`（變體 A 兩種插入序 / 變體 B 落盤與順序無關 / 三層混合存活 / 隔離拷貝 / 祖先子樹隔離）

**嚴重性**: 🟡 中等

**類型**: 配置系統

---

### [BUG-036] 平台切段消息的命令尾部參數靜默丟失

**問題**: 平台把一條消息切成多個 text 段（如 `/kick` 與參數之間夾著 mention 段、或輸入法分段）時，命令分發只取第一個 text 段做匹配——`/艾特 @xxx 123` 解析為無參數的 `艾特`，聲明了 `args=` 的命令直接報"參數缺失"，且無任何留痕。
**原因**: `command.py` 的文本提取循環取到首個 `type=="text"` 段後 `break`，其餘段（含全部非文本段）被丟棄。
**影響版本**: 2.6.0（命令分發引入）- 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: 命令文本改為按段順序收集全部 text 段空格拼接；mention/圖片夾層不再導致命令整體無法解析；同步補齊畸形段容錯（`message` 為 None/字串/非 dict 段不再擊穿分發器）。
**回歸測試**: tests/unit/test_unit_command_multiseg.py

**嚴重性**: 🟡 中等
**類型**: 事件系統

### [BUG-037] 被拒絕命令經 alt_message 整鏈重跑：重複回覆與權限函數副作用雙觸發

**問題**: 適配器的 `alt_message` 與消息段文本不一致時（如 alt 含 @文本前綴），命中命令被 scope/ACL/master/permission 拒絕後，分發器用 alt_message 把整條鏈重跑一遍——用戶收到兩條"權限不足"回覆，自定義權限函數（常帶查庫/計數副作用）被調用兩次。
**原因**: 拒絕路徑 `return False` 與"未命中命令"共用同一返回值，分發器據此認為可嘗試 alt 兜底；而事件在拒絕前已被認領，重跑僅多執行了回覆與權限判定。
**影響版本**: 2.9.0（治理/權限鏈成形）- 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: 文本處理改三態契約（unmatched/consumed/rejected）——命中註冊命令後（無論拒絕與否）不再 alt 回退；僅未命中任何命令時保持 alt 兜底。
**回歸測試**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**嚴重性**: 🟡 中等
**類型**: 事件系統

### [BUG-038] 命令處理器內註冊的 wait_reply 被同一條觸發消息立即消費

**問題**: 命令執行體內調用 `wait_reply` / 註冊交互等待時，等待被同一條命令消息立即命中——交互流首問被跳過，"用戶回覆"實為命令文本本身（答非所問/數據污染）。
**原因**: `_handle_message` 在方法開頭與結尾各調用一次 `interaction.resolve`，命令執行後結尾的二次 resolve 會命中執行期間新註冊的等待；cmdpass 關閉時 alt 缺失場景判定為空串直接放行，加重了該問題。
**影響版本**: 2.8.0（交互會話系統引入）- 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: 分發鏈收斂為單次 `interaction.resolve`（方法開頭處），刪除結尾二次調用；等待統一由下一條消息消費。
**回歸測試**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**嚴重性**: 🟡 中等
**類型**: 事件系統

### [BUG-039] select() 同鍵多路等待後者靜默取消前者

**問題**: `event.select()` 的多條期望推導出同一會話鍵（同 user 不同 pattern、多條 session 期望等）時，後註冊路把先註冊路以"衝突"取消，select 直接拋 `InteractionCancelled` 而非文檔承諾的超時返回 `(None, None)`。
**原因**: 每路獨立調用 `interaction.register`，其互斥語義對同鍵舊等待發 `REASON_CONFLICT` 取消；註釋聲稱"同 user 多路因事件副本獨立互不衝突"不成立——副本只改 user_id，同 user 多路的鍵完全相同。
**影響版本**: 2.9.0（select 引入）- 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: select 改為聚合等待——全部期望合併為自定義 matcher 的單條目（按鍵集合登記、共享同一 future），任一路命中即返回對應下標；同鍵多路天然共存。
**回歸測試**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**嚴重性**: 🟡 中等
**類型**: 事件系統

### [BUG-040] BaseConverter.at() 產出 OB11 遺留 "at" 段，全框架 mention 判定不識別

**問題**: 適配器用 `BaseConverter.at()` 組裝入站事件時，`must_at_bot` / `has_mention()` / `on_at_message` 全部失明——@機器人命令在群里靜默失效。
**原因**: `at()` 產出 `{"type": "at"}`（OB11 形態），而框架全部 mention 判定與構建側（MessageBuilder/發送修飾器）均為 OB12 的 `"mention"`，雙軌並存且無任何告警。
**影響版本**: 引入版本不早於 2.5.0 - 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: `at()` 改產 `{"type": "mention", "data": {"user_id": ...}}`（方法名保留別名，新增 `mention` 別名）。
**回歸測試**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**嚴重性**: 🟡 中等
**類型**: 適配器

### [BUG-041] 無 alt_message 的適配器上交互原語永久超時、命令穿透失效

**問題**: 適配器只填 message 段不填 `alt_message` 時：`confirm` / `choose` / `collect` 對用戶明文回覆（如"是"）永久等待；等待期間的已註冊命令永遠無法穿透執行；`Event.get_text()` 返回空串導致腳手架示例靜默失效。
**原因**: 上述路徑全部直取 `alt_message` 字串、無消息段回退——框架"alt_message 為適配器可選字段"的契約下，僅段填充是合法形態。
**影響版本**: 各交互原語引入版本 - 2.10.0
**修復版本**: 2.10.1-dev.0
**修復內容**: 統一走 `alt_message` 优先 + text 段回退的 `extract_text` 口徑（交互原語五處取值/校驗點、cmdpass 判定、`Event.get_text()/get_message_text()`）。
**回歸測試**: tests/unit/test_unit_command_multiseg.py

**嚴重性**: 🟡 中等
**類型**: 事件系統

### [BUG-042] 聲明式配置模板的嵌套子表頭漂移為頂層表

**問題**: 嵌套 dataclass 聲明的配置（ConfigClass 內嵌 dataclass 字段）首次生成配置模板時，子表頭 `[Nested]` 落在文件頂層而非組件節內——適配器讀 `cfg.嵌套字段` 拿不到值；`config.full.example` 中同樣錯位。
**原因**: 模板生成器對嵌套 dataclass 渲染相對表頭（`[Nested]`），而 TOML 表頭語義是從根算起的絕對路徑；`setConfigTemplate` 舊實現把解析後的表對象搬進組件節、`full.example` 直接文本拼裝，兩條路徑都未把相對表頭重錨到組件路徑下。
**影響版本**: 2.10.0 - 2.10.1（嵌套 dataclass 模板渲染隨該版本引入）
**修復版本**: 2.10.2-dev.0
**修復內容**: `setConfigTemplate` 按模板解析出的子表路徑集合精確重錨表頭（`[Nested]` → `[組件名.Nested]`）；`config.full.example` 生成側改傳 `_prefix` 直接產出絕對表頭。
**回歸測試**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**嚴重性**: 🟡 中等
**類型**: 配置系統 / 適配器