# 異常體系與捕獲指南

ErisPulse 所有自定義異常都繼承自 `ErisPulseError`，底層庫異常（aiohttp、aiomysql 等）會在框架內部被捕獲並轉換為對應的 ErisPulse 異常——業務代碼**無需依賴任何底層庫異常類型**。

{!--< tips >!--}
1. 想寬泛兜底：捕獲 `ErisPulseError`（所有框架異常的基類）
2. 想精確處理：按模組捕獲（如 `ModuleCallTimeoutError`、`StorageUnreachableError`）
3. 存儲操作預設不拋出：失敗時記錄日誌並返回 `False / None / default`
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
├── ModuleError                     # 模組系統異常基類（Core/module）
│   └── ModuleCallError             # 模組間調用異常基類
│       ├── ModuleNotAvailableError # 目標模組未註冊/未啟用/載入失敗
│       ├── ServiceNotProvidedError # 目標模組未宣告該服務（meta.services 白名單外）
│       └── ModuleCallTimeoutError  # 被調方法執行超時（預設 30s）
└── （框架內部錯誤）                 # ValueError 等用於參數校驗，見下文
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
| `StorageUnreachableError` | 建池階段 | 資料庫不可達 / 憑證錯誤 / 網路隔離，重試耗盡 |

> **儲存操作的失敗語義**：KV 與查詢操作**預設不拋出**——失敗時記錄 ERROR 日誌並
> 返回 `False` / `None` / `default`（避免連接問題阻塞框架運行）。`StorageUnreachableError`
> 主要用於框架內部冷卻與重連判定；需要精確感知失敗時，檢查返回值即可。

連接失敗行為詳見[儲存後端 → 連接失敗行為](storage-backends.md#連接失敗行為)。

### Interaction — `Core/Event/interaction.py`

`wait_reply` / 會話租約 / 提醒定時器相關：

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `InteractionError` | 交互會話層 | 交互會話異常基類 |

等待被取消（模組卸載 / 平台關閉 / 同會話新等待取代）時，`wait_reply` **返回 `None`**
而不拋出異常；會話租約被佔用則由 `hold()` 拋 `SessionOccupiedError`（繼承自
`InteractionError`）。

### Module 系列 — `Core/module.py`（`sdk.module.call`）

| 異常 | 發生位置 | 典型場景 |
|------|----------|----------|
| `ModuleError` | 模組系統 | 模組系統異常基類 |
| `ModuleCallError` | `module.call()` | 模組間呼叫異常基類 |
| `ModuleNotAvailableError` | `module.call()` | 目標未註冊 / 未啟用 / 加載失敗 |
| `ServiceNotProvidedError` | `module.call()` | 目標 `meta.services` 白名單未宣告該方法 |
| `ModuleCallTimeoutError` | `module.call()` | 被調協程超過超時時間（預設 30s） |

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

儲存查詢建構器的參數校驗（空欄位類型、`Insert` 非 dict、不安全欄位類型等）拋標準
`ValueError`——這類屬於**開發期編碼錯誤**，正常業務程式碼不應捕獲，而應修正呼叫。

## 捕獲建議

```python
from ErisPulse.Core import ErisPulseError  # 基類已從 Core 聚合導出

try:
    ...
except ErisPulseError as e:
    ...  # 統一兜底：所有框架自定義異常
```

- 模組開發：按需精確捕獲（上表），最外層可用 `ErisPulseError` 兜底
- 異常均已從 `ErisPulse.Core` 聚合導出，也可從 `ErisPulse.Core.Bases.errors` 導入
- 完整定義見 `src/ErisPulse/Core/Bases/errors.py`