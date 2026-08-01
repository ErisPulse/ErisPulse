# 配置檔說明
> 這個文件會介紹框架的配置檔，如果有第三方模組需要配置，請參考模組的文件。

ErisPulse 使用 TOML 格式的配置檔 `config/config.toml` 來管理專案配置。

## 配置檔位置

配置檔位於專案根目錄的 `config/` 資料夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 配置載入錯誤處理

框架在載入 `config.toml` 時會區分三種錯誤狀態，並提供**可操作的診斷資訊**，而不是靜默回退到預設配置：

| 錯誤狀態 | 觸發條件 | 框架行為 |
|---------|---------|---------|
| 檔案缺失 | `config.toml` 不存在 | 正常首次啟動，靜默使用空配置（不發出警告） |
| TOML 語法錯誤 | 檔案存在但格式非法（如少了引號、括號未閉合） | 輸出**錯誤行號/列號與原因**，並提示已回退預設配置 |
| 權限/其他錯誤 | 無讀取權限、IO 錯誤等 | 輸出**明確原因**，並提示已回退預設配置 |

例如，當你不小心把配置寫成了 `port = 8000`（少了引號的字串）時，日誌會輸出類似：

```
[ERROR] [Config] 配置檔 config/config.toml 語法錯誤（第 3 行 第 1 列）: ...
[WARNING] [Config] 已回退到預設配置，您的自訂設定未生效——請修復後重新啟動
```

這樣你可以在**預設 INFO 級別**下立刻定位問題，而不會困惑「為什麼我改的設定沒生效」。

> **執行中改壞配置檔？** 如果你在機器人執行期間手動編輯 `config.toml` 引入了語法錯誤，框架在下次寫入（合併設定）時會輸出「配置檔已損壞（語法錯誤，第 X 行），無法合併寫入——請先修復配置檔後重新啟動」，而不是令人困惑的「寫入失敗」。待寫入的設定項目會被保留，不會遺失。

## 環境變數覆蓋

框架支援用環境變數**覆蓋** `ErisPulse.*` 設定項（適合 Docker / 容器化 / CI 部署，無需修改 `config.toml`）。

命名規則：把點分路徑 `ErisPulse.<section>.<key>` 改為全大寫、`.` 替換為 `_`，並加上 `ERISPULSE_` 前綴：

| 設定項 | 環境變數 | 範例值 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

行為說明：
- **優先級最高**：環境變數覆蓋「配置檔」與「預設值」，按原值類型自動轉換（`bool` / `int` / `float` / 逗號分隔的 `list` / 字串）
- **不持久化**：覆蓋只在執行期生效，不會寫回 `config.toml`
- **支援熱更新**：執行中修改環境變數後，配合設定監聽的重載即可生效

```bash
# Docker 部署範例：不修改 config.toml，直接覆蓋端口
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` 這類框架設定走 `get_server_config()` 等 API 讀取，均受環境變數覆蓋影響。

## 設定熱更新

從 2.7.0 起，框架對設定熱更新做了**系統化支援**。外部修改 `config.toml` 後（背景 watcher 每 5 秒檢測一次），或程式碼呼叫 `setConfig()` 後，各組件自動響應：

| 組件 | 支援熱更新的設定 | 行為 |
|------|----------------|------|
| **日誌 Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | 自動重新應用（帶變更檢測） |
| **命令系統 CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 下一條訊息即生效 |
| **適配器併發** | `framework.handler_max_concurrency` | 失效快取信號量，按新值重建 |
| **主動 GC** | `framework.proactive_gc_interval` | 每輪重讀，支援執行時調整/禁用 |
| **模組/適配器設定** | 各自的設定項 | 觸發 `on_config_update(old, new)` 回呼 |

**需重新啟動的設定**（無法安全熱切換，變更時會輸出告警「需重新啟動程序後生效」）：

| 設定 | 原因 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件在服務啟動時寫入 FastAPI，執行時無法安全熱切換 |
| `storage.use_global_db` | SQLite 檔案句柄已在執行時開啟，切換路徑不安全 |

> **中途編輯儲存出錯？** 若編輯 `config.toml` 時出現瞬時語法錯誤，框架會**保留上次有效設定**並輸出診斷日誌，不會把空設定廣播給各組件（避免 `on_config_update` 收到空值誤回退預設）。

## 完整設定示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## 伺服器設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| ssl_certfile | string | 空 | SSL 證書檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |

## 日誌設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌等級：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE 為最低等級，輸出框架內部詳細除錯資訊） |
| format | string | rich | 日誌輸出格式，預設使用 rich 彩色輸出 |
| log_files | array | 空 | 日誌輸出檔案清單 |
| memory_limit | integer | 1000 | 內存中保存的日誌條數 |

## 框架設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶載入 |
| uninit_timeout | integer | 30 | 優雅關閉的總超時時間（秒），超過後強制終止。0 表示不設超時 |
| strict_mode | integer | 0 | 嚴格模式等級，見下方「嚴格模式」說明 |

### 嚴格模式

嚴格模式控制模組/適配器在載入階段不合規或失敗時的處理策略。現代模組/適配器都應繼承對應的基類（`BaseModule`/`BaseAdapter`），未繼承基類的組件會影響框架的上下文系統與兜底清理，可能導致資源洩漏。

> **2.5.2 變更**：預設等級從 `1`（跳過）調整為 `0`（寬鬆），以減少新使用者初次使用時遇到的載入問題。未繼承基類的組件將以 WARNING 提示並嘗試載入，而非直接拒絕。如需恢復旧行為，請顯式設定 `strict_mode = 1`。

| 等級 | 名稱 | 行為 |
|------|------|------|
| 0 | 寬鬆（預設） | 違規僅警告，未繼承基類的組件仍會嘗試載入（相容舊組件） |
| 1 | 嚴格-跳過 | 拒絕未繼承基類的組件並跳過，其餘正常啟動 |
| 2 | 嚴格-致命 | 收集所有違規後統一報告並中止整個啟動 |

各等級下，「載入/註冊/初始化階段報錯」這類組件自身崩潰始終會被跳過；區別在於：

- **0 → 1**：唯一行為變化是「未繼承基類」從「仍載入」變為「跳過」。
- **1 → 2**：所有違規（未繼承基類、載入失敗、註冊失敗、初始化失敗等）升級為致命，會在啟動檢查點收集後一次性輸出違規清單並中止。

#### 豁免清單

如果某些組件確實暫時無法遷移（例如依賴的舊模組），可以將其加入豁免清單，被列名的組件即使不合規也會按寬鬆模式對待，繼續載入：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> 當某個組件被嚴格模式拒絕時，日誌會明確提示如何恢復載入（加入豁免清單或調低等級）。

## 儲存設定

```toml
[ErisPulse.storage]
use_global_db = false
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（包內）而非專案資料庫。`true` 時所有專案共享 ErisPulse 包內的 SQLite 資料庫；`false`（預設）時每個專案使用 `config/` 目錄下獨立的資料庫 |

## 事件設定

### 命令設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| prefix | string | / | 命令前綴 |
| case_sensitive | boolean | true | 是否區分大小寫（`/Help` 與 `/help` 是否為不同命令） |
| allow_space_prefix | boolean | false | 是否允許空格作為前綴 |
| must_at_bot | boolean | false | 是否必須@機器人才能觸發命令（私聊不受限制） |

### 消息設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的訊息 |

## 國際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| language | string | auto | 框架內建文本的顯示語言。設為 `auto` 自動檢測系統語言，也可設為具體代碼：`zh-CN`、`zh-TW`、`en`、`ja`、`ru` |

## 模組設定

每個模組可以在設定檔中定義自己的設定：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模組中讀取和寫入設定：

```python
from ErisPulse import sdk

# 讀取設定
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 運行時寫入設定（延遲儲存）
sdk.config.setConfig("MyModule.timeout", 60)

# 立即儲存到檔案
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` 預設採用延遲寫入（約每 5 秒批量儲存到檔案），設定 `immediate=True` 可立即持久化。設定變更會觸發 `config.set` 生命週期事件。

## 下一步

- [CLI 命令參考](cli-reference.md) - 了解所有命令列命令
- [開發者指南](../developer-guide/) - 學習開發自訂模組