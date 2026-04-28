# Bug 追蹤器

本文檔記錄 ErisPulse SDK 的已知 Bug 和修復情況。

---

## 已修復的 Bug

### [BUG-001] Init 指令適配器配置路徑類型錯誤

**問題**: 使用 `ep init` 指令進行互動式初始化時，選擇配置適配器會出現類型錯誤：

```
互動式初始化失敗: unsupported operand type(s) for /: 'str' and 'str'
```

**原因**: 2.3.7 版本調整配置檔路徑時，方法參數類型不一致。`_configure_adapters_interactive_sync` 接收 `str` 類型參數，但內部使用 `Path` 的 `/` 運算子拼接路徑。

**影響版本**: 2.3.7 - 2.3.9-dev.1

**修復版本**: 2.3.9-dev.1

**修復內容**: 將 `_configure_adapters_interactive_sync` 方法的參數類型從 `str` 改為 `Path`，呼叫時直接傳遞 `Path` 物件。

**修復日期**: 2026/03/23

---

### [BUG-002] 重啟後指令事件失效

**問題**: 呼叫 `sdk.restart()` 後，透過 `@command` 註冊的指令無法被觸發，表現為發送指令後機器人無響應。

**原因**: `adapter.shutdown()` 清空事件總線後，`BaseEventHandler` 的 `_linked_to_adapter_bus` 狀態未重置為 `False`，導致 `_process_event` 方法認為已經掛載到適配器總線，跳過重新掛載操作。

**影響版本**: 2.2.x - 2.4.0-dev.2

**修復版本**: 2.4.0-dev.3

**修復內容**: 引入 `_linked_to_adapter_bus` 狀態追蹤，`_clear_handlers()` 斷開總線連接後，下次 `register()` 自動重新掛載，適配 shutdown/restart 場景。

**修復日期**: 2026/04/09

---

### [BUG-003] 生命週期事件處理器未清理

**問題**: `sdk.restart()` 後，舊的生命週期事件處理器仍然存在並重複觸發，導致同一個事件被多次處理。

**原因**: `lifecycle._handlers` 字典在 `uninit()` 時從未被清理，restart 後舊處理器與新處理器同時存在。

**影響版本**: 2.3.0 - 2.4.0-dev.2

**修復版本**: 2.4.0-dev.3

**修復內容**: 在 `Uninitializer` 的清理流程末尾（所有事件提交之後），清空 `lifecycle._handlers`。

**修復日期**: 2026/04/09

---

### [BUG-004] Event.confirm() 確認詞集合賦值重複

**問題**: `Event.confirm()` 方法中，`_yes`、`_no`、`_all` 三個變數的賦值代碼被完全重複了兩次（共6行），導致無意義的重複計算。

**原因**: 代碼複製貼上錯誤。

**影響版本**: 2.4.0-dev.4

**修復版本**: 2.4.2-dev.1

**修復內容**: 刪除 `wrapper.py` 中 739-741 行的重複賦值代碼。

**修復日期**: 2026/04/13

---

### [BUG-005] MessageBuilder.at 方法定義被覆蓋（死代碼）

**問題**: `MessageBuilder` 類中 `at` 方法被定義了三次：一個實例方法、一個靜態方法、最後被 `_DualMethod` 賦值覆蓋。前兩個定義是永遠不會被執行的死代碼。

**原因**: 重構為 `_DualMethod` 雙模式描述符時，忘記刪除舊的手動定義。

**影響版本**: 2.4.0-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 刪除 `message_builder.py` 中 159-181 行的兩個死 `at` 方法定義，只保留 `_DualMethod` 賦值。

**修復日期**: 2026/04/13

---

### [BUG-006] Event.is_friend_add/is_friend_delete 的 detail_type 與 OB12 標準不一致

**問題**: `Event.is_friend_add()` 檢查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 檢查 `detail_type == "friend_delete"`，但 OneBot12 標準定義的 `detail_type` 值為 `"friend_increase"` 和 `"friend_decrease"`。與 `notice.py` 中 `on_friend_add`/`on_friend_remove` 裝飾器使用的值不一致，導致透過裝飾器註冊的處理器觸發時，對應的 `is_friend_add()`/`is_friend_delete()` 判斷方法返回 `False`。

**原因**: `wrapper.py` 中使用了非標準的命名，而 `notice.py` 使用了正確的 OB12 標準命名。

**影響版本**: rq實裝至今

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `is_friend_add()` 的匹配值從 `"friend_add"` 改為 `"friend_increase"`，`is_friend_delete()` 從 `"friend_delete"` 改為 `"friend_decrease"`。

**修復日期**: 2026/04/13

---

### [BUG-007] adapter.clear() 未清理 _started_instances 導致重啟後狀態不正確

**問題**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、處理器和 `_bots`，但遺漏了 `_started_instances` 集合。如果適配器正在運行時呼叫 `clear()`，`_started_instances` 會保留懸空引用，導致重啟後狀態判斷錯誤。

**原因**: 2.4.0-dev.1 引入 `_started_instances` 時未在 `clear()` 中同步清理。

**影響版本**: 2.4.0-dev.1 - 2.4.2-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 在 `clear()` 方法中添加 `self._started_instances.clear()`。

**修復日期**: 2026/04/13

---

### [BUG-008] command.wait_reply() 使用已棄用的 asyncio.get_event_loop()

**問題**: `CommandHandler.wait_reply()` 方法使用 `asyncio.get_event_loop()` 建立 future 和獲取時間戳，該方法在 Python 3.10+ 中已棄用，在非同步上下文中應使用 `asyncio.get_running_loop()`。與同檔案中 `wrapper.py` 的 `wait_for()` 方法使用的 `get_running_loop()` 不一致。

**原因**: 開發時使用了舊版 API，後續新增的 `wait_for()` 使用了正確的 API 但未回溯修復舊代碼。

**影響版本**: 2.3.0-dev.0

**修復版本**: 2.4.2-dev.1

**修復內容**: 將 `command.py` 中兩處 `asyncio.get_event_loop()` 替換為 `asyncio.get_running_loop()`。

**修復日期**: 2026/04/13

---

### [BUG-009] Event.collect() 字段缺少 key 時靜默跳過

**問題**: `Event.collect()` 方法在遍歷字段列表時，如果某個字段字典缺少 `key`，會靜默跳過該字段，不輸出任何日誌或警告。開發者如果拼寫錯誤（如 `"Key"` 而非 `"key"`），整個字段會被悄悄忽略，導致下游行為難以排查。

**原因**: 缺少輸入驗證和錯誤反饋。

**影響版本**: 2.4.0-dev.4

**修復版本**: 2.4.2-dev.1

**修復內容**: 在跳過前添加 `logger.warning()` 記錄缺少 `key` 的字段資訊。

**修復日期**: 2026/04/13

---

### [BUG-010] LazyModule 同步存取 BaseModule 導致未初始化完成

**問題**: 使用者在同步上下文中存取懶載入的 BaseModule 屬性時，模組使用 `loop.create_task()` 非同步初始化但不等待，導致屬性存取時可能未初始化完成，引發競態條件。

**原因**: `_ensure_initialized()` 對 BaseModule 使用 `loop.create_task(self._initialize())` 後立即返回，未確保初始化完成。

**影響版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**: 在同步上下文中，BaseModule 的初始化改為使用 `asyncio.run(self._initialize())`，確保初始化完成後再返回。保持透明代理特性，使用者無需感知同步/非同步差異。

**修復日期**: 2026/04/21

---

### [BUG-011] 配置系統多線寫入導致資料遺失

**問題**: 在多線程環境下，多個線程同時呼叫 `config.setConfig()` 時，`_flush_config()` 讀取-修改-寫入操作不是原子性的，可能導致部分寫入遺失。

**原因**: `_flush_config()` 雖然使用了 `RLock`，但檔案讀取和寫入之間沒有檔案鎖保護，且 `_schedule_write` 的 Timer 可能被多次觸發導致覆蓋。

**影響版本**: 2.3.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**:
1. 添加檔案鎖機制（`_file_lock`）確保檔案操作原子性
2. 使用暫存檔案寫入後原子性重新命名（`os.replace`/`os.rename`）
3. 改進 `_schedule_write` 的 Timer 取消和重新排程邏輯

**修復日期**: 2026/04/21

---

### [BUG-012] SDK 屬性存取錯誤資訊不準確

**問題**: 存取不存在的屬性時，錯誤提示"您可能使用了錯誤的SDK註冊物件"，可能誤導使用者，實際可能是模組未啟用或名稱拼寫錯誤。

**原因**: `__getattribute__` 的錯誤資訊沒有區分不同場景，統一給出模糊的提示。

**影響版本**: 2.0.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**: 根據屬性名稱區分不同場景：
1. 已註冊但未啟用：提示模組/適配器未啟用
2. 完全不存在：提示檢查名稱拼寫
同時將原始 AttributeError 重新拋出，便於上層捕捉。

**修復日期**: 2026/04/21

---

### [BUG-013] Uninitializer 對未初始化 LazyModule 的清理邏輯過於複雜

**問題**: `Uninitializer` 為從未被存取過的 LazyModule 建立臨時實例來呼叫 `on_unload`，代碼複雜且容易出錯。

**原因**: 企圖為所有 LazyModule 呼叫生命週期方法，但未初始化的模組不需要也不應該被初始化。

**影響版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修復版本**: 2.4.2-dev.2

**修復內容**: 簡化清理邏輯，只處理已初始化的 LazyModule：
1. 跳過未初始化的 LazyModule，不建立臨時實例
2. 只為已初始化的模組呼叫 `on_unload`
3. 刪除複雜的臨時實例建立邏輯

**修復日期**: 2026/04/21

---

### [BUG-014] Windows 下 CTRL+C 無法停止程式

**問題**: 在 Windows 上直接執行 `python main.py` 時，按下 CTRL+C 無法終止程式。程式正常啟動並輸出路由伺服器資訊後，CTRL+C 完全無響應，只能透過工作管理員強殺進程。而透過 `epsdk run` 啟動時可以正常停止——但 `epsdk run` 是透過子進程模型執行的。

**原因**: Hypercorn ASGI 伺服器的 `serve()` 函數內部透過 `signal.signal(SIGINT, handler)` 註冊了自己的 SIGINT 處理器，覆蓋了 Python 預設的 `KeyboardInterrupt` 處理機制。當透過 `asyncio.create_task()` 啟動 Hypercorn 作為後台任務時，Hypercorn 的內部 shutdown 流程無法正常觸發（因為它期望的是 `worker_serve` 模式），導致 CTRL+C 訊號被 Hypercorn 吞掉但會引發任何清理動作。

**影響版本**: [2.3.6 - 2.4.2]

**修復版本**: 2.4.3-dev.0

**修復內容**:
1. 將 ASGI 伺服器從 Hypercorn 切換為 Uvicorn（`pyproject.toml` 依賴變更）
2. 使用 `uvicorn.Server._serve()` 直接啟動伺服器，**繞過** `capture_signals()` 訊號處理上下文管理器
3. 透過 `server.should_exit = True` 實現優雅停止，超時則取消後台任務
4. 同步移除子進程執行模型和 `runtime/cleanup.py` 清理模組（子進程清理機制不再需要）

**修復日期**: 2026/04/28