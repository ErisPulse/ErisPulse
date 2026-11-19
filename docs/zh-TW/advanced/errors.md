# 錯誤體系與捕獲指南

> [!NOTE]
> **L1 核心必讀**——首頁「閱讀路徑」中的五篇核心文件之一，模組開發必備。

ErisPulse 所有自定義錯誤都繼承自 `ErisPulseError`，底層庫異常（aiohttp、aiomysql 等）會在框架內部被捕獲並轉換為對應的 ErisPulse 錯誤——業務代碼**無需依賴任何底層庫錯誤類型**。

{!--< tips >!--}
1. 想寬泛兜底：捕獲 `ErisPulseError`（所有框架錯誤的基類）
2. 想精確處理：按模組捕獲（如 `ModuleCallTimeoutError`、`StorageOperationError`、`StorageUnreachableError`）
3. 存儲寫操作失敗**預設拋出** `StorageOperationError`（2.12 起）；連接級不可達的冷卻期快速失敗仍返回 `False / None / default`，連接狀態變化訂閱 `storage.unreachable` / `storage.recovered` 事件
{!--< /tips >!--}

## 異常總覽

```text
ErisPulseError                      # 所有框架異常的基類
├── ClientError                     # HTTP/WS 客戶端請求異常基類（Core/client）
│   ├── ClientConnectionError       # 連接層錯誤：DNS 解析失敗、連接被拒、網路不可達
│   ├── ClientTimeoutError          # 請求超時
│   └── HTTPStatusError             # HTTP 狀態碼錯誤（如 4xx/5xx 且 raise_for_status）
├── WebSocketError                  # WebSocket 異常基類（Core/client 的 WS 連接）
│   └── WebSocketDisconnect         # WebSocket 斷開連接（服務端/客戶端通用）
├── ConnectionRegistryError         # 連接註冊表異常基類（Core/connections，2.10+）
│   ├── ConnectionNotFoundError     # 連接不存在/已斷開註銷（connections.get/close）
│   └── ConnectionPermissionError   # 非 owner 關閉他人連接（關閉權歸創建者）
├── StorageError                    # 存儲異常基類（Core/storage）
│   ├── StorageOperationError       # 存儲操作執行失敗（2.12 起寫路徑預設拋出）
│   └── StorageUnreachableError     # 存儲後端不可達（建池重試耗盡：資料庫不可達/憑證錯誤）
├── InteractionError                # 交互會話異常基類（Core/Event/interaction）
│   ├── InteractionCancelled        # 掛起的等待/租約被取消（wait_reply 上層轉為返回 None）
│   └── SessionOccupiedError        # 會話互斥租約被占用（hold() 获取失敗）
├── ModuleError                     # 模塊系統異常基類（Core/module）
│   └── ModuleCallError             # 模塊間調用異常基類
│       ├── ModuleNotAvailableError # 目標模組未註冊/未啟用/初始化失敗（含懶加載訪問）
│       ├── ServiceNotProvidedError # 目標模組未聲明該服務（meta.services 白名單外）
│       └── ModuleCallTimeoutError  # 被調方法執行超時（預設 30s）
├── ShadowError                     # 影子模組異常基類（Core/shadow）
│   ├── ShadowStateError            # 狀態不滿足：目標未加載/已有活躍影子/未綁定影子（start/dismiss）
│   ├── ShadowSourceError           # 影子源不可用：路徑不存在/加載器缺失/裝載失敗（start）
│   └── ShadowPromoteError          # 轉正失敗：影子未註冊/未加載/加載器無快照/重載失敗（promote）
└── StrictModeError                 # 嚴格模式致命違規（中止啟動流程，loaders/strict）
```

## 結構化屬性

捕獲異常後可讀取結構化屬性（無需解析訊息文本）：

| 異常 | 屬性 |
|------|------|
| `ClientError`（含子類） | `.url` 請求 URL、`.method` 請求方法、`.attempts` 已嘗試次數（重試耗盡時） |
| `HTTPStatusError` | `.status` 狀態碼、`.message` 回應訊息 |
| `WebSocketDisconnect` | `.code` 關閉碼、`.reason` 關閉原因 |
| `ConnectionNotFoundError` | `.connection_id` 查找的連接 id |
| `ConnectionPermissionError` | `.connection_id` 目標連接 id、`.owner` 連接歸屬 owner |
| `StorageUnreachableError` | `.backend` 後端名（sqlite/mysql/postgres）、`.cooldown` 冷卻秒數 |
| `StorageOperationError` | `.operation` 操作名（set/delete/clear/set_multi/transaction_begin）、`.key` 操作鍵 |
| `ModuleCallError`（含子類） | `.module` 目標模組名、`.method` 目標方法名 |
| `ModuleCallTimeoutError` | 繼承 `.module/.method`，另有 `.timeout` 超時時限（秒） |
| `InteractionCancelled` | `.reason` 取消原因、`.wait_key` 會話鍵 |
| `SessionOccupiedError` | `.wait_key` 會話鍵、`.owner` 佔用者 |
| `StrictModeError` | `.violations` 違規記錄列表 |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"請求失敗 {e.method} {e.url}，共嘗試 {e.attempts} 次: {e}")
```

## 各異常說明與發生位置

### Client 系列 — `Core/client.py` / `Core/Bases/client.py`

`sdk.client` / HTTP 客戶端與 WebSocket 客戶端發起請求時拋出：

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `ClientError` | 請求封裝層 | 其它客戶端錯誤（底層 aiohttp 異常已轉換） |
| `ClientConnectionError` | 連接建立階段 | 目標服務不可達、DNS 失敗、連接被拒 |
| `ClientTimeoutError` | 請求執行階段 | 超過請求超時時間 |
| `HTTPStatusError` | `raise_for_status()` | 响應狀態碼為 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### WebSocket 系列 — `Core/client.py`（`send` / `receive`）

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `WebSocketError` | WS 收發方法 | 連接已關閉、收到意外消息類型、底層 WS 異常 |
| `WebSocketDisconnect` | WS 收發方法 | 對端正常斷開連接（框架會自動重連） |

### 連接註冊表系列 — `Core/connections.py`（2.10+）

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | 連接 id 不存在或已斷開註銷 |
| `ConnectionPermissionError` | 非 owner 調用 `conn.close()` | 跨模組關閉他人連接（發送與分組不受限） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `StorageError` | 存儲層 | 存儲相關異常基類 |
| `StorageOperationError` | KV 寫路徑 / 事務開啟（2.12 起） | 寫鎖競爭超時 / SQL 錯誤 / 約束衝突 / 事務開啟超時——**預設拋出** |
| `StorageUnreachableError` | 建池階段 | 資料庫不可達 / 憑證錯誤 / 網路隔離，重試耗盡 |

> **儲存操作的失敗語義（2.12 起分層）**：
> - **寫路徑執行失敗預設拋出** `StorageOperationError`（`aset` / `adelete` / `aclear` / `set_multi`
>   及同步橋同路徑）——庫可達而寫失敗意味著資料未寫入，靜默返回會讓呼叫方無感知丟資料；
>   重要寫入請 try/except 並做補償
> - **連接級不可達**（冷卻期快速失敗）仍返回 `False` / `None` / `default`（框架韌性語義），
>   業務程式碼通常不會捕獲到 `StorageUnreachableError`；執行時感知連接狀態請訂閱生命週期事件
>   `storage.unreachable` / `storage.recovered`（詳見[生命週期事件](lifecycle.md#儲存連接狀態)）
> - **事務開啟超過 30s** 抛 `StorageOperationError`（`STORAGE_TXN_BEGIN_TIMEOUT_SECS`）——
>   併發長事務無限死等屬框架缺陷，必須可觀測

連接失敗行為詳見[儲存後端 → 連接失敗行為](storage-backends.md#連接失敗行為)。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / 會話租約 / 提醒定時器相關：

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `InteractionError` | 交互會話層 | 交互會話異常基類 |
| `InteractionCancelled` | 掛起等待被取消時 | 設置到等待 future 上（等待方可捕獲獲取 `.reason`） |
| `SessionOccupiedError` | `hold()` 租約獲取失敗 | 會話已被其他 owner 占用（`.owner` 可查占用者） |

等待被取消（模組卸載 / 平台關閉 / 同會話新等待取代）時，`wait_reply` **返回 `None`**
而不拋出異常（`InteractionCancelled` 在內部被轉換）；需要區分取消原因時才直接捕獲它。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `ModuleError` | 模組系統 | 模組系統異常基類 |
| `ModuleCallError` | `module.call()` | 模組間呼叫異常基類 |
| `ModuleNotAvailableError` | `module.call()` / 懶加載屬性訪問 | 目標未註冊 / 未啟用 / 初始化失敗 |
| `ServiceNotProvidedError` | `module.call()` | 目標 `meta.services` 白名單未聲明該方法 |
| `ModuleCallTimeoutError` | `module.call()` | 被調協程超過超時時間（預設 30s） |

"目標模組不可用"在不同訪問路徑下的異常類型：

| 訪問路徑 | 異常 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（類型化） |
| `sdk.module.X.attr`（懶加載屬性訪問，初始化失敗後） | `ModuleNotAvailableError` |
| `sdk.module.X`（模組未啟用時的屬性訪問） | `AttributeError`（Python 屬性慣例，`hasattr` 依賴此語義） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目標模組不存在 / 未啟用
except ServiceNotProvidedError:
    ...  # 目標模組未提供該服務
```

### Shadow 系列 — `Core/shadow.py`（影子模組）

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `ShadowError` | 影子模組機制 | 影子異常基類（統一捕獲所有影子錯誤） |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | 目標未加載 / 已有活躍影子 / 未綁定影子 |
| `ShadowSourceError` | `shadow_start()` | 源路徑不存在 / 插件加載器缺失 / 源無可加載類 / 裝載失敗 |
| `ShadowPromoteError` | `promote_shadow()` | 影子未註冊 / 未加載 / 加載器不支援快照 / 轉正重載失敗 |

### 框架內部參數校驗（ValueError）

儲存查詢建構器的參數校驗（空列類型、`Insert` 非 dict、不安全列類型等）拋標準
`ValueError`——這類屬於**開發期編碼錯誤**，正常業務程式碼不應捕獲，而應修正呼叫。

適配器標準動作失敗**不拋異常**：返回帶 `retcode` 的響應字典（協定語義，如
`retcode=10002` 表示動作未實現）——與 client 層"失敗拋 `ClientError`"是兩條並行
的錯誤通道，適配器開發時需同時處理。

## 捕獲建議

```python
from ErisPulse.Core import ErisPulseError  # 基類已從 Core 聚合導出

try:
    ...
except ErisPulseError as e:
    ...  # 統一兜底：所有框架自定義異常
```

- 模組開發：按需精確捕獲（上表），最外層可用 `ErisPulseError` 兜底
- 異常均已從 `ErisPulse.Core` 聚合導出（含 `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`），也可從 `ErisPulse.Core.Bases.errors` 導入
- 完整定義見 `src/ErisPulse/Core/Bases/errors.py`

## 關閉噪音折疊

長期駐留進程在關閉（或背景循環被取消）時，事件循環常會刷出一批無處理價值的
`Task was destroyed but it is pending!` 類解釋器噪音。框架內建**同類噪音折疊**：
2 秒視窗內的同類訊息降級為 TRACE 並合併計數，只輸出一次，結尾帶
「（另有 N 次同類訊息被折疊）」後綴。這是刻意的降噪行為——看到折疊後綴不代表
框架吞掉了真實異常，業務異常（上表各類）照常完整輸出。折疊僅針對解釋器退出噪音，
業務異常不受影響。什麼級別的異常值得留痕、什麼可以降級/折疊，遵循
[工程健壯性規則 · 異常留痕分級](../styleguide/engineering.md#1-異常留痕分級)。

## 相關文件

依排查意圖選擇：

- **儲存操作回傳 `False` / `None`，想知道連線狀態** → [儲存後端 · 連線失敗行為](storage-backends.md#連線失敗行為)，或訂閱 [storage.unreachable / storage.recovered 事件](lifecycle.md#儲存連線狀態)
- **`wait_reply` 回傳 `None`，想知道被什麼取消** → [互動會話系統](interaction.md)（取消原因對照表）
- **`module.call` 抛模組呼叫異常** → [模組間通訊](module-communication.md)
- **連線 / WebSocket 報錯** → [網路客戶端](client.md)（ClientError 體系）與[連線池與廣播](connections.md)（連線註冊表異常）