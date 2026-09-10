# 錯誤體系與捕獲指南

ErisPulse 所有自訂的錯誤都繼承自 `ErisPulseError`，底層庫的錯誤（aiohttp、aiomysql 等）會在框架內部被捕獲並轉換為對應的 ErisPulse 錯誤——業務程式碼**不需要依賴任何底層庫的錯誤類型**。

{!--< tips >!--}
1. 想要廣泛兜底：捕獲 `ErisPulseError`（所有框架錯誤的基類）
2. 想要精確處理：按模組捕獲（如 `ModuleCallTimeoutError`、`StorageUnreachableError`）
3. 儲存操作預設不拋出：失敗時記錄日誌並返回 `False / None / default`；連線狀態變化訂閱 `storage.unreachable` / `storage.recovered` 事件
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
├── StorageError                    # 存儲異常基類（Core/storage）
│   └── StorageUnreachableError     # 存儲後端不可達（建池重試耗盡：資料庫不可達/憑證錯誤）
├── InteractionError                # 交互會話異常基類（Core/Event/interaction）
│   ├── InteractionCancelled        # 掛起的等待/租約被取消（wait_reply 上層轉為返回 None）
│   └── SessionOccupiedError        # 會話互斥租約被佔用（hold() 獲取失敗）
├── ModuleError                     # 模塊系統異常基類（Core/module）
│   └── ModuleCallError             # 模塊間調用異常基類
│       ├── ModuleNotAvailableError # 目標模組未註冊/未啟用/初始化失敗（含懶加載訪問）
│       ├── ServiceNotProvidedError # 目標模組未聲明該服務（meta.services 白名單外）
│       └── ModuleCallTimeoutError  # 被調方法執行超時（預設 30s）
└── StrictModeError                 # 嚴格模式致命違規（中止啟動流程，loaders/strict）
```

## 結構化屬性

捕獲異常後可讀取結構化屬性（無需解析訊息文字）：

| 異常 | 屬性 |
|------|------|
| `ClientError`（含子類） | `.url` 請求 URL、`.method` 請求方法、`.attempts` 已嘗試次數（重試耗盡時） |
| `HTTPStatusError` | `.status` 狀態碼、`.message` 回應訊息 |
| `WebSocketDisconnect` | `.code` 關閉碼、`.reason` 關閉原因 |
| `StorageUnreachableError` | `.backend` 後端名（sqlite/mysql/postgres）、`.cooldown` 冷卻秒數 |
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
| `WebSocketError` | WS 收發方法 | 連接已關閉、收到意外訊息類型、底層 WS 異常 |
| `WebSocketDisconnect` | WS 收發方法 | 對端正常斷開連接（框架會自動重連） |

### Storage 系列 — `Core/storage` / `Core/Bases/sql_base.py`

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `StorageError` | 存儲層 | 存儲相關異常基類 |
| `StorageUnreachableError` | 建池階段 | 數據庫不可達 / 憑證錯誤 / 網路隔離，重試耗盡 |

> **存儲操作的失敗語義**：KV 與查詢操作**預設不拋出**——失敗時記錄 ERROR 日誌並
> 返回 `False` / `None` / `default`（避免連接問題阻塞框架運行）。因此業務程式碼通常
> **不會**捕獲到 `StorageUnreachableError`（它主要供直接操作存儲底層或自訂後端使用）。
> 運行時感知連接狀態請訂閱生命週期事件 `storage.unreachable` / `storage.recovered`
> （詳見[生命週期事件](lifecycle.md#存儲連接狀態)）。
> 連接失敗行為詳見[存儲後端 → 連接失敗行為](storage-backends.md#連接失敗行為)。

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
| `ModuleNotAvailableError` | `module.call()` / 慢加載屬性存取 | 目標未註冊 / 未啟用 / 初始化失敗 |
| `ServiceNotProvidedError` | `module.call()` | 目標 `meta.services` 白名單未聲明該方法 |
| `ModuleCallTimeoutError` | `module.call()` | 被調協程超過超時時間（預設 30s） |

"目標模組不可用"在不同存取路徑下的異常類型：

| 存取路徑 | 異常 |
|----------|------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError`（類型化） |
| `sdk.module.X.attr`（慢加載屬性存取，初始化失敗後） | `ModuleNotAvailableError` |
| `sdk.module.X`（模組未啟用時的屬性存取） | `AttributeError`（Python 屬性慣例，`hasattr` 依賴此語義） |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # 目標模組不存在 / 未啟用
except ServiceNotProvidedError:
    ...  # 目標模組未提供該服務
```

### 框架內部參數校驗（ValueError）

存儲查詢建構器的參數校驗（空欄位類型、`Insert` 非 dict、不安全欄位類型等）拋標準
`ValueError`——這類屬於**開發期編碼錯誤**，正常業務程式碼不應捕獲，而應修正呼叫。

適配器標準動作失敗**不拋異常**：返回帶 `retcode` 的響應字典（協定語義，如
`retcode=10002` 表示動作未實現）——與 client 層"失敗拋 `ClientError`"是兩條平行
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